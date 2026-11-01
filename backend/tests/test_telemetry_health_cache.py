import asyncio
import json
from contextlib import asynccontextmanager
from types import SimpleNamespace
from uuid import UUID

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.exc import SQLAlchemyError

from app import main
from app.telemetry import incident_producer
from app.telemetry.health_cache_producer import CacheSampler, STATE_KEY
from app.telemetry.health_completion import HealthCompletionMiddleware
from app.telemetry.request_completion import RequestCompletionMiddleware, REQUEST_ID_KEY
from app.telemetry.schemas import TelemetryReceipt
from app.telemetry.server import ServerQueue
from test_telemetry_incident_producer import settings
from test_telemetry_shared import shared


def test_counter_windows_delays_resets_invalid_and_rejection(monkeypatch):
    async def run():
        service=incident_producer.IncidentProducer(shared(settings()))
        now=[0];cache=SimpleNamespace(hits=10,misses=20,bypasses=30)
        sampler=CacheSampler(service,cache,clock=lambda:now[0])
        cache.hits=15;cache.misses=22;cache.bypasses=31;now[0]=300
        assert sampler.cut()
        first=json.loads(service.queue.pending[-1][2])
        assert first['properties']==dict(jurisdiction=None,environment='test',hits=5,misses=2,bypasses=1,windowSeconds=300)
        assert first['userId'] is None and first['sessionId'] is None and first['requestId'] is None
        now[0]=650.9;assert sampler.cut()
        assert json.loads(service.queue.pending[-1][2])['properties']['windowSeconds']==350
        assert json.loads(service.queue.pending[-1][2])['properties']['hits']==0
        before=len(service.queue.pending);cache.hits=1;now[0]=950
        assert not sampler.cut() and len(service.queue.pending)==before
        cache.hits=4;now[0]=1250;assert sampler.cut()
        assert json.loads(service.queue.pending[-1][2])['properties']['hits']==3
        cache.misses=float('nan');now[0]=1550;assert not sampler.cut()
        cache.misses=22;now[0]=1850;assert not sampler.cut()  # rebase after invalid sample
        now[0]=2150;assert sampler.cut()
        original=service.queue.enqueue;monkeypatch.setattr(service.queue,'enqueue',lambda *args:False)
        cache.hits=9;now[0]=2450;assert not sampler.cut()
        monkeypatch.setattr(service.queue,'enqueue',original)
        cache.hits=10;now[0]=2750;assert sampler.cut()
        assert json.loads(service.queue.pending[-1][2])['properties']['hits']==1
        assert (cache.hits,cache.misses,cache.bypasses)==(10,22,31)
        await sampler.close();await service.close()
    asyncio.run(run())


def test_sampler_interval_and_lifecycle_without_real_sleep():
    async def run():
        service=incident_producer.IncidentProducer(shared(settings()));gate=asyncio.Event();delays=[];now=[0]
        async def sleep(delay):delays.append(delay);await gate.wait();gate.clear()
        cache=SimpleNamespace(hits=0,misses=0,bypasses=0)
        sampler=CacheSampler(service,cache,clock=lambda:now[0],sleep=sleep)
        service.cache_sampler=sampler.start();sampler.start()
        await asyncio.sleep(0);assert delays==[300]
        cache.hits=2;now[0]=300;gate.set();await asyncio.sleep(0)
        assert len(service.queue.pending)==1 and delays==[300,300]
        task=sampler.task;await service.close()
        assert task.done() and sampler.task is None and sampler.previous is None and service.cache_sampler is None
        assert service.queue.counts['discarded']==1  # no extra partial window on close
    asyncio.run(run())


@pytest.mark.parametrize('case',['health','connected','absent','sql','io','timeout'])
def test_real_health_routes_keep_contracts_and_observed_outcomes(monkeypatch,case):
    async def run():
        received=[];statements=[]
        async def sink(body):
            batch=json.loads(body);received.extend(batch['events']);return TelemetryReceipt(received=len(batch['events']))
        service=incident_producer.IncidentProducer(shared(settings()),queue=ServerQueue(sink=sink))
        monkeypatch.setattr(incident_producer,'_producer',service)
        class Connection:
            async def execute(self,statement):statements.append(str(statement))
        class Engine:
            @asynccontextmanager
            async def connect(self):
                if case=='sql':raise SQLAlchemyError('Synthetic sensitive details')
                if case=='io':raise OSError('Synthetic sensitive details')
                if case=='timeout':raise TimeoutError('Synthetic sensitive details')
                yield Connection()
        monkeypatch.setattr(main,'engine',None if case=='absent' else Engine())
        async with AsyncClient(transport=ASGITransport(app=main.app),base_url='http://test') as client:
            response=await client.get('/health' if case=='health' else '/status')
            expected=200 if case in ['health','connected'] else 503
            assert response.status_code==expected and 'x-request-id' not in response.headers
            assert response.json()==({'status':'ok'} if case=='health' else {'status':'ok','database':'connected'} if case=='connected' else {'status':'error','database':'unavailable'})
            await service.queue.flush();assert len(received)==1
            e=received[0];assert e['event_type']=='service_health_checked' and e['userId'] is None
            assert e['properties']['check']==('liveness' if case=='health' else 'database')
            assert e['properties']['outcome']==('ok' if expected==200 else 'timeout' if case=='timeout' else 'failed')
            assert e['properties']['jurisdiction'] is None and e['properties']['durationMs']>=0
            assert isinstance(UUID(e['requestId']),UUID)
            assert 'sensitive' not in json.dumps(e) and 'sensitive' not in response.text
            assert statements==(['SELECT 1'] if case=='connected' else [])
        await service.close()
    asyncio.run(run())


@pytest.mark.parametrize('failure',[None,'send','cancel','query','capture'])
def test_final_send_only_and_correlated_id(monkeypatch,failure):
    async def run():
        calls=[];clock=iter([1,1.125])
        monkeypatch.setattr('app.telemetry.health_completion.monotonic',lambda:next(clock))
        def capture(*args):
            calls.append(args)
            if failure=='capture':raise RuntimeError('Synthetic capture failure')
        monkeypatch.setattr('app.telemetry.health_completion.capture_health',capture)
        async def application(scope,receive,send):
            scope['state'][STATE_KEY]=('database','failed')
            if failure=='query':raise RuntimeError('Synthetic exception')
            await send({'type':'http.response.start','status':503,'headers':[]})
            await send({'type':'http.response.body','body':b'[','more_body':True});assert not calls
            await send({'type':'http.response.body','body':b']'})
            assert calls==[('database','failed',125,scope['state'][REQUEST_ID_KEY])]
        async def send(message):
            if message['type']=='http.response.body' and not message.get('more_body'):
                if failure=='send':raise OSError('Synthetic disconnect')
                if failure=='cancel':raise asyncio.CancelledError()
        app=RequestCompletionMiddleware(HealthCompletionMiddleware(application));scope={'type':'http'}
        if failure in ['send','cancel','query']:
            with pytest.raises(OSError if failure=='send' else asyncio.CancelledError if failure=='cancel' else RuntimeError):
                await app(scope,None,send)
            assert not calls
        else:await app(scope,None,send);assert len(calls)==1
        assert scope['state']=={}
    asyncio.run(run())


@pytest.mark.integration
def test_real_postgresql_status_and_optional_sampler(monkeypatch):
    from app.core.config import get_settings
    from app.db.session import engine
    from app.telemetry.schemas import TelemetryBatch
    config=get_settings()
    if config.database_url is None or not config.require_database_url().endswith('/telemetry_validation'):
        pytest.skip('Dedicated synthetic telemetry_validation database required')
    config=shared(config.model_copy(deep=True));monkeypatch.setattr(incident_producer,'get_settings',lambda:config)
    async def run():
        async with main.app.router.lifespan_context(main.app):
            service=incident_producer._producer;received=[]
            assert service.cache_sampler.task is not None
            async def sink(body):
                batch=TelemetryBatch.model_validate_json(body);received.extend(e for e in batch.events if e.event_type != 'data_integrity_checked')
                return TelemetryReceipt(received=len(batch.events))
            service.queue.sink=sink
            async with AsyncClient(transport=ASGITransport(app=main.app),base_url='http://test') as client:
                assert (await client.get('/health')).status_code==200
                assert (await client.get('/status')).status_code==200
                while service.queue.pending:await service.queue.flush()
                assert len(received)==2 and {e.properties.check for e in received}=={'liveness','database'}
                assert all(e.properties.jurisdiction is None and e.properties.outcome=='ok' for e in received)
                async def broken(body):raise RuntimeError('Synthetic sink failure')
                service.queue.sink=broken
                assert (await client.get('/status')).status_code==200
                await service.queue.flush();assert service.queue.counts['discarded']==1
            sampler=service.cache_sampler;task=sampler.task
        assert task.done() and sampler.task is None
        await engine.dispose()
    asyncio.run(run())


def test_optional_start_is_idempotent_and_stop_cancels_sampler(monkeypatch):
    async def run():
        monkeypatch.setattr(incident_producer, '_producer', None)
        monkeypatch.setattr(incident_producer, 'get_settings', lambda: shared(settings()))
        service = incident_producer.start()
        sampler = service.cache_sampler; task = sampler.task
        assert incident_producer.start() is service and service.cache_sampler.task is task
        await incident_producer.stop()
        assert task.done() and sampler.task is None and incident_producer._producer is None
    asyncio.run(run())
