import asyncio
import json
from uuid import UUID, uuid4

import pytest

from app.auth.dependencies import Actor
from app.telemetry import request_producer, incident_producer
from app.telemetry.request_completion import RequestCompletionMiddleware
from app.telemetry.schemas import TelemetryReceipt
from app.telemetry.server import ServerQueue
from test_telemetry_incident_producer import settings
from test_telemetry_shared import shared


@pytest.mark.parametrize('status',[200,204,400,500])
def test_final_response_measurement_and_private_id(monkeypatch,status):
    async def run():
        calls=[];sent=[];actor=Actor(uuid4(),'admin');clinic=uuid4()
        clock=iter([10,10.125])
        monkeypatch.setattr('app.telemetry.request_completion.monotonic',lambda:next(clock))
        monkeypatch.setattr('app.telemetry.request_completion.capture_request',lambda *args:calls.append(args))
        async def app(scope,receive,send):
            scope['state'][request_producer.STATE_KEY]=(actor,clinic)
            await send({'type':'http.response.start','status':status,'headers':[]})
            await send({'type':'http.response.body','body':b'[','more_body':True});assert not calls
            await send({'type':'http.response.body','body':b']'})
        async def send(message):sent.append(message.copy());assert not calls
        external=str(uuid4());scope={'type':'http','headers':[(b'x-request-id',external.encode())]}
        await RequestCompletionMiddleware(app)(scope,None,send)
        assert len(calls)==1 and calls[0][:2]==(actor,clinic)
        assert isinstance(calls[0][2],UUID) and str(calls[0][2])!=external
        assert calls[0][3:5]==(status,125)
        assert sent[0]['headers']==[] and [x['body'] for x in sent[1:]]==[b'[',b']']
        assert request_producer.STATE_KEY not in scope['state']
    asyncio.run(run())


@pytest.mark.parametrize('failure',['query','serialization','send','cancel','missing','capture'])
def test_incomplete_or_missing_context_and_capture_fault(monkeypatch,failure):
    async def run():
        calls=[]
        def capture(*args):calls.append(args);raise RuntimeError('Synthetic capture failure')
        monkeypatch.setattr('app.telemetry.request_completion.capture_request',capture)
        async def app(scope,receive,send):
            if failure=='query':raise RuntimeError('Synthetic query failure')
            if failure!='missing':scope['state'][request_producer.STATE_KEY]=(Actor(uuid4(),'admin'),uuid4())
            if failure=='serialization':raise RuntimeError('Synthetic serialization failure')
            await send({'type':'http.response.start','status':200,'headers':[]})
            await send({'type':'http.response.body','body':b'[]'})
        async def send(message):
            if message['type']=='http.response.body':
                if failure=='send':raise OSError('Synthetic disconnect')
                if failure=='cancel':raise asyncio.CancelledError()
        scope={'type':'http'}
        if failure in ['missing','capture']:await RequestCompletionMiddleware(app)(scope,None,send)
        else:
            error=asyncio.CancelledError if failure=='cancel' else OSError if failure=='send' else RuntimeError
            with pytest.raises(error):await RequestCompletionMiddleware(app)(scope,None,send)
        assert len(calls)==(1 if failure=='capture' else 0)
        assert request_producer.STATE_KEY not in scope['state']
    asyncio.run(run())


@pytest.mark.parametrize('failure',[None,'timeout','inactive'])
def test_bounded_regional_capture(monkeypatch,failure):
    async def run():
        gate=asyncio.Event();batches=[];actor=Actor(uuid4(),'admin');clinic=uuid4();request_id=uuid4()
        async def resolve(*args,**kwargs):
            await gate.wait()
            if failure=='timeout':await asyncio.sleep(1)
            if failure=='inactive':raise ValueError('Synthetic inactive clinic')
            return 'opaque','UK'
        monkeypatch.setattr(request_producer,'resolve_clinic',resolve)
        async def sink(body):
            batch=json.loads(body);batches.append(batch);return TelemetryReceipt(received=len(batch['events']))
        service=incident_producer.IncidentProducer(shared(settings()),queue=ServerQueue(sink=sink))
        monkeypatch.setattr(incident_producer,'_producer',service)
        for _ in range(16):assert request_producer.capture_request(actor,clinic,request_id,200,125,'2026-11-01T00:00:00Z')
        assert not request_producer.capture_request(actor,clinic,request_id,200,125,'2026-11-01T00:00:00Z')
        gate.set();await asyncio.gather(*service.tasks);await service.queue.flush()
        if failure:assert not batches and service.discarded==17
        else:
            e=batches[0]['events'][0]
            assert e['properties']==dict(jurisdiction='UK',environment='test',route='incidents',statusCode=200,durationMs=125)
            assert e['userId']==request_producer.user_id(request_producer.region_settings(service.settings,'UK'),actor.id)
            assert e['requestId']==str(request_id) and e['sessionId'] is None
            assert all(str(value) not in json.dumps(batches) for value in [actor.id,clinic])
        await service.close();assert not service.tasks and service.queue.closed
    asyncio.run(run())


@pytest.mark.integration
def test_real_four_read_routes_us_uk_and_denials(monkeypatch):
    from app.core.config import get_settings
    from app.main import app
    from app.auth import security
    from app.auth.security import create_access_token
    from app.db.session import engine
    from httpx import AsyncClient,ASGITransport
    from app.telemetry.schemas import TelemetryBatch
    from test_telemetry_shared import US,UK
    config=get_settings()
    if config.database_url is None or not config.require_database_url().endswith('/telemetry_validation'):
        pytest.skip('Dedicated synthetic telemetry_validation database required')
    config=shared(config.model_copy(deep=True))
    for module in [incident_producer,security]:monkeypatch.setattr(module,'get_settings',lambda:config)
    async def run():
        async with app.router.lifespan_context(app):
            service=incident_producer._producer;received=[]
            async def sink(body):
                batch=TelemetryBatch.model_validate_json(body);received.extend(e for e in batch.events if e.event_type not in {'authentication_succeeded', 'authentication_failed', 'authorization_denied', 'service_health_checked', 'catalog_cache_observed', 'data_integrity_checked'})
                return TelemetryReceipt(received=len(batch.events))
            service.queue.sink=sink
            async def drain():
                await asyncio.gather(*service.tasks)
                while service.queue.pending:await service.queue.flush()
            actor=uuid4();headers={'Authorization':'Bearer '+create_access_token(actor,'admin')}
            async with AsyncClient(transport=ASGITransport(app=app),base_url='http://test') as client:
                ids={}
                for name in ['entryChannel','incidentType','severity']:
                    ids[name]=(await client.get('/catalogs/'+name,headers=headers)).json()['values'][0]['id']
                for clinic,region,juris,system in [(US,'US','00000000-0000-0000-0000-000000000001','00000000-0000-0000-0000-000000000301'),(UK,'UK','00000000-0000-0000-0000-000000000002','00000000-0000-0000-0000-000000000304')]:
                    payload=dict(title='Synthetic HTTP telemetry',description='Synthetic fixture',clinic_id=str(clinic),jurisdiction_id=juris,affected_system_id=system,responsible_area_id='00000000-0000-0000-0000-000000000201',entry_channel_value_id=ids['entryChannel'],incident_type_value_id=ids['incidentType'],severity_value_id=ids['severity'])
                    response=await client.post('/incidents',json=payload,headers=headers);assert response.status_code==201
                    identity=response.json()['id'];await drain();received.clear()
                    for suffix in ['', '/history','/assignment-history','/audit']:
                        result=await client.get('/incidents/'+identity+suffix,headers={**headers,'X-Request-Id':str(clinic)})
                        assert result.status_code==200 and 'x-request-id' not in result.headers
                        await drain()
                    http=[e for e in received if e.event_type=='api_request_completed']
                    assert len(http)==4 and len({e.requestId for e in http})==4
                    assert all(e.properties.jurisdiction==region and e.properties.statusCode==200 and e.properties.durationMs>=0 for e in http)
                    assert len([e for e in received if e.event_type=='audit_accessed'])==1
                    assert all(str(value) not in json.dumps([e.model_dump() for e in received]) for value in [actor,clinic,identity])
                    before=len(received)
                    for url,auth,expected in [('/incidents/'+identity,{},401),('/incidents/'+str(uuid4()),headers,404),('/incidents/not-a-uuid',headers,422),('/incidents/'+identity,{'Authorization':'Bearer '+create_access_token(uuid4(),'responsibleArea',area_id=UUID('00000000-0000-0000-0000-000000000202'))},403)]:
                        assert (await client.get(url,headers=auth)).status_code==expected
                    for url in ['/health','/status','/incidents','/management/audit-events']:
                        assert (await client.get(url,headers=headers)).status_code==200
                    await drain();assert len(received)==before+2
                    before=len(received)
                    async def broken(body):raise RuntimeError('Synthetic sink failure')
                    service.queue.sink=broken
                    assert (await client.get('/incidents/'+identity,headers=headers)).status_code==200
                    await drain();assert len(received)==before
                    service.queue.sink=sink
        await engine.dispose()
    asyncio.run(run())
