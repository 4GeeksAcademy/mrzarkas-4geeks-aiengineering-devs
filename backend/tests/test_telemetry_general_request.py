"""Anonymous completed health/status responses and safe ASGI boundaries."""
import asyncio
import json
from uuid import uuid4
from contextlib import asynccontextmanager
import pytest
from app.telemetry import incident_producer, request_producer
from app.telemetry.request_completion import RequestCompletionMiddleware, REQUEST_ID_KEY
from app.telemetry.schemas import TelemetryReceipt
from app.telemetry.server import ServerQueue
from test_telemetry_incident_producer import settings
from test_telemetry_shared import shared
from test_telemetry_context import telemetry

@pytest.mark.parametrize('case',['stream','send-failure','cancel','incomplete','duplicate','capture-failure','unmarked','clinical'])
def test_asgi_general_completion(monkeypatch,case):
    async def run():
        calls=[];clinical=[]
        clock=iter([10,10.125])
        monkeypatch.setattr('app.telemetry.request_completion.monotonic',lambda:next(clock))
        def capture(*args):
            calls.append(args)
            if case=='capture-failure': raise RuntimeError('synthetic')
        monkeypatch.setattr('app.telemetry.request_completion.capture_general_request',capture)
        monkeypatch.setattr('app.telemetry.request_completion.capture_request',lambda *args:clinical.append(args))
        async def app(scope,receive,send):
            if case!='unmarked': scope['state'][request_producer.GENERAL_STATE_KEY]='health'
            if case=='clinical': scope['state'][request_producer.STATE_KEY]=('synthetic-actor','synthetic-clinic')
            await send({'type':'http.response.start','status':200,'headers':[]})
            await send({'type':'http.response.body','body':b'a','more_body':True})
            assert not calls
            if case!='incomplete':
                await send({'type':'http.response.body','body':b'b'})
                if case=='duplicate': await send({'type':'http.response.body','body':b''})
        async def send(message):
            if message['type']=='http.response.body' and not message.get('more_body',False):
                if case=='send-failure': raise OSError('synthetic')
                if case=='cancel': raise asyncio.CancelledError()
        scope={'type':'http','headers':[(b'x-request-id',b'caller-id')]}
        if case in {'send-failure','cancel'}:
            with pytest.raises(OSError if case=='send-failure' else asyncio.CancelledError):
                await RequestCompletionMiddleware(app)(scope,None,send)
        else: await RequestCompletionMiddleware(app)(scope,None,send)
        assert len(calls)==(1 if case in {'stream','duplicate','capture-failure'} else 0)
        assert len(clinical)==(1 if case=='clinical' else 0)
        if calls: assert calls[0][3]==125
        assert not any(k in scope['state'] for k in [request_producer.STATE_KEY,request_producer.GENERAL_STATE_KEY,REQUEST_ID_KEY])
    asyncio.run(run())


def test_http_anonymous_health_status_and_failure(monkeypatch):
    from httpx import ASGITransport,AsyncClient
    import app.main as main
    async def run():
        events=[]
        async def sink(body):
            batch=json.loads(body);events.extend(batch['events']);return TelemetryReceipt(received=len(batch['events']))
        service=incident_producer.IncidentProducer(shared(settings()),queue=ServerQueue(sink=sink))
        monkeypatch.setattr(incident_producer,'_producer',service)
        class Engine:
            @asynccontextmanager
            async def connect(self):
                yield self
            async def execute(self,*args): pass
        async with AsyncClient(transport=ASGITransport(app=main.app),base_url='http://test') as client:
            headers={'X-Request-Id':'caller-id','Authorization':'Bearer deliberately-invalid-synthetic'}
            monkeypatch.setattr(main,'engine',Engine())
            health=await client.get('/health',headers=headers)
            status=await client.get('/status',headers=headers)
            monkeypatch.setattr(main,'engine',None)
            failure=await client.get('/status',headers=headers)
            assert health.status_code==status.status_code==200 and failure.status_code==503
            assert health.json()=={'status':'ok'} and status.json()=={'status':'ok','database':'connected'}
            assert failure.json()=={'status':'error','database':'unavailable'}
            assert (await client.get('/not-a-route')).status_code==404
            while service.tasks: await asyncio.gather(*service.tasks)
            while service.queue.pending: await service.queue.flush()
        api=[e for e in events if e['event_type']=='api_request_completed']
        assert len(api)==3 and len({e['requestId'] for e in api})==3
        assert [(e['properties']['route'],e['properties']['statusCode']) for e in api]==[('health',200),('status',200),('status',503)]
        assert all(e['userId'] is None and e['sessionId'] is None and e['properties']['jurisdiction'] is None for e in api)
        assert all(set(e['properties'])=={'jurisdiction','environment','route','statusCode','durationMs'} for e in api)
        assert 'caller-id' not in json.dumps(api) and 'deliberately-invalid-synthetic' not in json.dumps(api)
        health_events=[e for e in events if e['event_type']=='service_health_checked']
        assert len(health_events)==3 and {e['requestId'] for e in health_events}=={e['requestId'] for e in api}
        await service.close()
    asyncio.run(run())

@pytest.mark.parametrize('case',['disabled','closed','route','id','status','nan','negative','saturated','sink'])
def test_optional_general_producer(monkeypatch,case):
    async def run():
        if case=='disabled':
            monkeypatch.setattr(incident_producer,'_producer',None)
            assert not request_producer.capture_general_request('health',uuid4(),200,1,'2026-11-03T00:00:00Z')
            return
        service=incident_producer.IncidentProducer(shared(settings()))
        monkeypatch.setattr(incident_producer,'_producer',service)
        if case=='closed': await service.close()
        if case=='saturated': monkeypatch.setattr(service.queue,'enqueue',lambda *args:False)
        accepted=request_producer.capture_general_request('unknown' if case=='route' else 'health',
            'bad' if case=='id' else uuid4(),0 if case=='status' else 200,
            float('nan') if case=='nan' else -1 if case=='negative' else 1,'2026-11-03T00:00:00Z')
        assert accepted==(case=='sink')
        if case=='sink':
            async def failure(*args): raise OSError('synthetic')
            service.queue.sink=failure
            await service.queue.flush()
        await service.close()
    asyncio.run(run())


def test_browser_rejects_general_api_fact(telemetry):
    from datetime import UTC,datetime
    _,request=telemetry
    context=request('/telemetry/context',{'clinicId':None}).json()
    event=dict(eventId=str(uuid4()),timestamp=datetime.now(UTC).isoformat(),schemaVersion='1.3.0',
        sessionId=context['sessionId'],userId=context['userId'],requestId=str(uuid4()),event_type='api_request_completed',
        properties=dict(jurisdiction=None,environment='test',route='health',statusCode=200,durationMs=1))
    assert request('/telemetry/events',{'events':[event]},headers={'X-Telemetry-Context':context['contextToken']}).status_code==403
