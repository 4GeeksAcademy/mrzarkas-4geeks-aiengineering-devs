import asyncio
import json
from uuid import UUID

import pytest
from httpx import AsyncClient, ASGITransport

from app import main
from app.telemetry import incident_producer, diagnostic_producer
from app.telemetry.diagnostic_producer import DiagnosticChannel, DIAGNOSTIC_EVENTS, diagnostic_sink, STATE_KEY
from app.telemetry.diagnostic_completion import DiagnosticCompletionMiddleware
from app.telemetry.request_completion import RequestCompletionMiddleware, REQUEST_ID_KEY
from app.telemetry.schemas import TelemetryReceipt
from app.telemetry.server import ServerQueue
from test_telemetry_incident_producer import settings
from test_telemetry_shared import shared
from test_telemetry_server import event, Clock
from test_telemetry_context import telemetry


def test_business_full_and_invalid_use_separate_anonymous_channel():
    async def run():
        service=incident_producer.IncidentProducer(shared(settings()))
        for _ in range(200):assert service.queue.enqueue(event(),'untrusted-scope-UK')
        assert not service.queue.enqueue(event(),'untrusted-scope-UK')
        diagnostic=json.loads(service.diagnostic_channel.queue.pending[-1][2])
        assert diagnostic['properties']==dict(jurisdiction='US',environment='test',reasonCode='queue_full',producer='api')
        invalid=event();invalid['properties'].update(jurisdiction='UK',title='Synthetic sensitive text')
        assert not service.queue.enqueue(invalid,'UK')
        diagnostic=json.loads(service.diagnostic_channel.queue.pending[-1][2])
        assert diagnostic['properties']==dict(jurisdiction=None,environment='test',reasonCode='schema',producer='api')
        assert diagnostic['userId'] is None and diagnostic['sessionId'] is None and diagnostic['requestId'] is None
        assert 'sensitive' not in json.dumps(diagnostic)
        assert len(service.queue.pending)==200 and len(service.diagnostic_channel.queue.pending)==2
        await service.close()
        assert not service.diagnostic_channel.queue.pending and service.diagnostic_channel.queue.closed
    asyncio.run(run())


@pytest.mark.parametrize('failure',['exception','timeout','ack'])
def test_terminal_batch_failure_one_diagnostic_per_validated_region(failure):
    async def run():
        async def sink(body):
            if failure=='exception':raise RuntimeError('Synthetic sensitive exception')
            if failure=='timeout':raise TimeoutError('Synthetic sensitive timeout')
            return TelemetryReceipt(received=999)
        service=incident_producer.IncidentProducer(shared(settings()),queue=ServerQueue(sink=sink))
        for _ in range(3):assert service.queue.enqueue(event(),'UK-untrusted-text')
        await service.queue.flush()
        assert service.queue.counts['discarded']==3 and len(service.diagnostic_channel.queue.pending)==1
        d=json.loads(service.diagnostic_channel.queue.pending[0][2])
        assert d['properties']==dict(jurisdiction='US',environment='test',producer='api',reasonCode='timeout' if failure=='timeout' else 'unavailable')
        assert d['requestId'] is None and 'sensitive' not in json.dumps(d)
        await service.close()
    asyncio.run(run())


def test_same_scope_different_validated_regions_never_mixes():
    async def run():
        async def sink(body):raise RuntimeError('Synthetic sink failure')
        service=incident_producer.IncidentProducer(shared(settings()),queue=ServerQueue(sink=sink))
        us=event();uk=event();uk['properties']['jurisdiction']='UK'
        service.queue.enqueue(us,'same-free-text');service.queue.enqueue(uk,'same-free-text')
        await service.queue.flush();await service.queue.flush()
        assert {json.loads(entry[2])['properties']['jurisdiction'] for entry in service.diagnostic_channel.queue.pending}=={'US','UK'}
        await service.close()
    asyncio.run(run())


def test_diagnostic_channel_failure_full_invalid_and_shutdown_do_not_recurse():
    async def run():
        channel=DiagnosticChannel(shared(settings()))
        assert channel.queue.allowed_events==DIAGNOSTIC_EVENTS and channel.queue.diagnostic_callback is None
        for _ in range(200):assert channel.capture('telemetry_delivery_failed',None,'unavailable')
        assert not channel.capture('telemetry_delivery_failed',None,'unavailable')
        assert not channel.queue.enqueue(event(),'US')
        assert channel.queue.counts['rejected']==2 and len(channel.queue.pending)==200
        calls=[]
        async def broken(body):calls.append(body);raise RuntimeError('Synthetic diagnostic failure')
        channel.queue.sink=broken
        await channel.queue.flush()
        assert len(calls)==1 and len(channel.queue.pending)==180 and channel.queue.counts['discarded']==20
        await channel.close()
        assert channel.queue.counts['discarded']==200 and not channel.queue.pending and channel.queue.task is None
        service=incident_producer.IncidentProducer(shared(settings()))
        async def wait(body):await asyncio.sleep(100)
        service.queue.sink=wait;service.queue.enqueue(event(),'US')
        flight=asyncio.create_task(service.queue.flush());await asyncio.sleep(0)
        flight.cancel();await asyncio.gather(flight,return_exceptions=True)
        assert not service.diagnostic_channel.queue.pending
        await service.close()
    asyncio.run(run())


def test_diagnostic_queue_has_twenty_and_first_ten_second_deadline():
    async def run():
        clock=Clock();batches=[]
        async def sink(body):
            value=json.loads(body);batches.append(value);return TelemetryReceipt(received=len(value['events']))
        channel=DiagnosticChannel(shared(settings()))
        await channel.queue.close()
        channel.queue=ServerQueue(sink=sink,loop=clock,allowed_events=DIAGNOSTIC_EVENTS)
        channel.capture('telemetry_contract_rejected',None,'schema');await clock.advance(9)
        channel.capture('telemetry_contract_rejected',None,'schema');await clock.advance(1)
        assert [len(batch['events']) for batch in batches]==[2]
        for _ in range(20):channel.capture('telemetry_contract_rejected',None,'schema')
        await clock.advance(0);assert [len(batch['events']) for batch in batches]==[2,20]
        await channel.close()
    asyncio.run(run())


@pytest.mark.parametrize('failure',[None,'send','cancel','query','capture','no-marker','wrong-status'])
def test_schema_diagnostic_only_after_complete_422(monkeypatch,failure):
    async def run():
        calls=[]
        def capture(*args):
            calls.append(args)
            if failure=='capture':raise RuntimeError('Synthetic capture failure')
        monkeypatch.setattr('app.telemetry.diagnostic_completion.capture_contract_rejection',capture)
        async def app(scope,receive,send):
            if failure!='no-marker':scope['state'][STATE_KEY]=True
            if failure=='query':raise RuntimeError('Synthetic query failure')
            await send({'type':'http.response.start','status':403 if failure=='wrong-status' else 422,'headers':[]})
            await send({'type':'http.response.body','body':b'[','more_body':True});assert not calls
            await send({'type':'http.response.body','body':b']'})
            if failure not in ['no-marker','wrong-status']:assert calls==[(scope['state'][REQUEST_ID_KEY],)]
        async def send(message):
            if message['type']=='http.response.body' and not message.get('more_body'):
                if failure=='send':raise OSError('Synthetic disconnect')
                if failure=='cancel':raise asyncio.CancelledError()
        scope={'type':'http'};middleware=RequestCompletionMiddleware(DiagnosticCompletionMiddleware(app))
        if failure in ['send','cancel','query']:
            with pytest.raises(OSError if failure=='send' else asyncio.CancelledError if failure=='cancel' else RuntimeError):
                await middleware(scope,None,send)
            assert not calls
        else:
            await middleware(scope,None,send)
            assert len(calls)==(0 if failure in ['no-marker','wrong-status'] else 1)
        assert scope['state']=={}
    asyncio.run(run())


def test_real_ingress_schema_rejection_keeps_response_and_does_not_reclassify_auth(monkeypatch,telemetry):
    async def run():
        config, _=telemetry;shared(config)
        service=incident_producer.IncidentProducer(config);received=[]
        monkeypatch.setattr(incident_producer,'_producer',service)
        async def sink(body):
            batch=json.loads(body);received.extend(batch['events']);return TelemetryReceipt(received=len(batch['events']))
        service.diagnostic_channel.queue.sink=sink
        from app.auth.security import create_access_token
        from test_telemetry_context import ACTOR
        headers={'Authorization':'Bearer '+create_access_token(ACTOR,'admin')}
        async with AsyncClient(transport=ASGITransport(app=main.app),base_url='http://test') as client:
            response=await client.post('/telemetry/events',json={'events':[{'jurisdiction':'UK','token':'synthetic-sensitive'}]},headers=headers)
            assert response.status_code==422 and response.json()=={'detail':'Invalid telemetry payload'}
            assert response.headers['cache-control']=='no-store'
            await service.diagnostic_channel.queue.flush();assert len(received)==1
            d=received[0];assert d['properties']==dict(jurisdiction=None,environment='test',reasonCode='schema',producer='api')
            assert d['userId'] is None and UUID(d['requestId']) and 'sensitive' not in json.dumps(d)
            assert (await client.post('/telemetry/events',json={'events':[]})).status_code==401
            assert (await client.post('/telemetry/context',json={'clinicId':None},headers={'Authorization':'Bearer synthetic-invalid'})).status_code==401
            await service.diagnostic_channel.queue.flush();assert len(received)==1
        await service.close()
    asyncio.run(run())


def test_diagnostic_sink_logs_counts_and_types_only(caplog):
    async def run():
        channel=DiagnosticChannel(shared(settings()))
        channel.capture('telemetry_delivery_failed','UK','unavailable')
        body=b'{"events":['+channel.queue.pending[0][2]+b']}'
        with caplog.at_level('INFO',logger='healthcore.telemetry.diagnostics'):
            assert (await diagnostic_sink(body)).received==1
        assert 'count=1' in caplog.text and 'telemetry_delivery_failed' in caplog.text
        assert 'unavailable' not in caplog.text and 'UK' not in caplog.text and 'eventId' not in caplog.text
        await channel.close()
    asyncio.run(run())


@pytest.mark.integration
def test_real_api_lifecycle_uses_independent_diagnostic_sink(monkeypatch):
    from app.core.config import get_settings
    from app.auth import security
    from app.auth.security import create_access_token
    from app.telemetry import router as telemetry_router
    from app.db.session import engine
    from app.telemetry.schemas import TelemetryBatch
    from test_telemetry_context import ACTOR
    config=get_settings()
    if config.database_url is None or not config.require_database_url().endswith('/telemetry_validation'):
        pytest.skip('Dedicated synthetic telemetry_validation database required')
    config=shared(config.model_copy(deep=True))
    for module in [incident_producer,security,telemetry_router]:monkeypatch.setattr(module,'get_settings',lambda:config)
    async def run():
        async with main.app.router.lifespan_context(main.app):
            service=incident_producer._producer;received=[]
            assert json.loads(service.queue.pending[0][2])['event_type']=='data_integrity_checked'
            await service.queue.flush()
            async def sink(body):
                batch=TelemetryBatch.model_validate_json(body);received.extend(batch.events)
                return TelemetryReceipt(received=len(batch.events))
            service.diagnostic_channel.queue.sink=sink
            async def broken(body):raise RuntimeError('Synthetic business sink failure')
            service.queue.sink=broken
            async with AsyncClient(transport=ASGITransport(app=main.app),base_url='http://test') as client:
                assert (await client.get('/status')).status_code==200
                await service.queue.flush()
                headers={'Authorization':'Bearer '+create_access_token(ACTOR,'admin')}
                assert (await client.post('/telemetry/events',json={'events':[]},headers=headers)).status_code==422
                while service.diagnostic_channel.queue.pending:await service.diagnostic_channel.queue.flush()
                assert {e.event_type for e in received}==DIAGNOSTIC_EVENTS
                assert all(e.properties.jurisdiction is None and e.userId is None for e in received)
                assert service.queue.counts['discarded']==1
            channel=service.diagnostic_channel
        assert channel.queue.closed and not channel.queue.pending and channel.queue.task is None
        await engine.dispose()
    asyncio.run(run())
