import asyncio
import json
import time
from uuid import uuid4, UUID

import pytest
from fastapi import FastAPI, Depends
from httpx import AsyncClient, ASGITransport

from app.auth.dependencies import Actor, get_current_actor, require_capability
from app.auth import security
from app.auth.security import create_access_token
from app.telemetry import security_producer, incident_producer
from app.telemetry.security_completion import SecurityCompletionMiddleware
from app.telemetry.request_completion import RequestCompletionMiddleware, REQUEST_ID_KEY
from app.telemetry.schemas import TelemetryReceipt
from app.telemetry.server import ServerQueue
from test_telemetry_incident_producer import settings
from test_telemetry_shared import shared


def test_actual_dependencies_deduplicate_and_keep_errors_anonymous(monkeypatch):
    async def run():
        config=shared(settings());received=[]
        monkeypatch.setattr(security,'get_settings',lambda:config)
        async def sink(body):
            batch=json.loads(body);received.extend(batch['events']);return TelemetryReceipt(received=len(batch['events']))
        service=incident_producer.IncidentProducer(config,queue=ServerQueue(sink=sink))
        monkeypatch.setattr(incident_producer,'_producer',service)
        app=FastAPI();app.add_middleware(RequestCompletionMiddleware);app.add_middleware(SecurityCompletionMiddleware)
        @app.get('/protected')
        async def protected(actor=Depends(get_current_actor)):return {'ok':True}
        @app.get('/denied')
        async def denied(actor=Depends(require_capability('catalog:manage'))):return {'ok':True}
        @app.get('/telemetry/events')
        async def excluded(actor=Depends(get_current_actor)):return {'ok':True}
        actor=uuid4();token=create_access_token(actor,'technology');headers={'Authorization':'Bearer '+token}
        async def drain():
            while service.queue.pending:await service.queue.flush()
        async with AsyncClient(transport=ASGITransport(app=app),base_url='http://test') as client:
            for _ in range(3):assert (await client.get('/protected',headers=headers)).status_code==200
            await drain();assert len(received)==1 and received[0]['event_type']=='authentication_succeeded'
            assert received[0]['userId']==security_producer.user_id(config,actor)
            assert received[0]['properties']==dict(jurisdiction=None,environment='test',channel='api')
            assert len(service.security_seen)==1
            assert all(token not in key and str(actor) not in key for key in service.security_seen)
            for auth,reason in [({},'missing'),({'Authorization':'Bearer synthetic-invalid'},'invalid'),({'Authorization':'Bearer '+create_access_token(uuid4(),'admin',expires_minutes=-1)},'expired')]:
                response=await client.get('/protected',headers=auth);assert response.status_code==401
                await drain();e=received[-1];assert e['event_type']=='authentication_failed' and e['userId'] is None
                assert e['properties']==dict(jurisdiction=None,environment='test',reasonCode=reason)
            response=await client.get('/denied',headers=headers)
            assert response.status_code==403 and response.json()=={'detail':"Role 'technology' lacks capability 'catalog:manage'"}
            await drain();e=received[-1];assert e['event_type']=='authorization_denied'
            assert e['properties']==dict(jurisdiction=None,environment='test',reasonCode='capability',operation='manage')
            before=len(received)
            assert (await client.get('/telemetry/events',headers={'Authorization':'Bearer '+create_access_token(uuid4(),'admin')})).status_code==200
            assert (await client.get('/telemetry/events')).status_code==401
            await drain();assert len(received)==before
            # New verified credential creates a different conceptual authentication.
            assert (await client.get('/protected',headers={'Authorization':'Bearer '+create_access_token(uuid4(),'admin')})).status_code==200
            await drain();assert received[-1]['event_type']=='authentication_succeeded'
            assert all(str(actor) not in json.dumps(e) and token not in json.dumps(e) for e in received)
            async def broken(body):raise RuntimeError('Synthetic sink failure')
            service.queue.sink=broken
            assert (await client.get('/protected')).status_code==401
            await drain();assert service.queue.counts['discarded']==1
        await service.close();assert service.security_seen=={}
    asyncio.run(run())


@pytest.mark.parametrize('status',[200,401,403,404,500])
def test_final_response_and_shared_request_id(monkeypatch,status):
    async def run():
        calls=[];scope={'type':'http','headers':[(b'x-request-id',str(uuid4()).encode())]}
        monkeypatch.setattr('app.telemetry.security_completion.capture_security',lambda *args:calls.append(args))
        async def application(scope,receive,send):
            scope['state'][security_producer.STATE_KEY]={'failure':'missing'}
            expected=scope['state'][REQUEST_ID_KEY]
            await send({'type':'http.response.start','status':status,'headers':[]})
            await send({'type':'http.response.body','body':b'[','more_body':True});assert not calls
            await send({'type':'http.response.body','body':b']'})
            assert len(calls)==1 and calls[0][1:]==(status,expected)
        sent=[]
        async def send(message):sent.append(message.copy());assert not calls
        app=SecurityCompletionMiddleware(RequestCompletionMiddleware(application))
        await app(scope,None,send)
        assert sent[0]['headers']==[] and scope['state']=={}
    asyncio.run(run())


@pytest.mark.parametrize('failure',['query','send','cancel','capture'])
def test_incomplete_and_capture_fault_are_isolated(monkeypatch,failure):
    async def run():
        calls=[]
        def capture(*args):calls.append(args);raise RuntimeError('Synthetic capture failure')
        monkeypatch.setattr('app.telemetry.security_completion.capture_security',capture)
        async def app(scope,receive,send):
            scope['state'][security_producer.STATE_KEY]={'failure':'missing'}
            if failure=='query':raise RuntimeError('Synthetic query failure')
            await send({'type':'http.response.start','status':401,'headers':[]})
            await send({'type':'http.response.body','body':b'[]'})
        async def send(message):
            if message['type']=='http.response.body':
                if failure=='send':raise OSError('Synthetic disconnect')
                if failure=='cancel':raise asyncio.CancelledError()
        scope={'type':'http'}
        if failure=='capture':await SecurityCompletionMiddleware(app)(scope,None,send)
        else:
            with pytest.raises(asyncio.CancelledError if failure=='cancel' else OSError if failure=='send' else RuntimeError):
                await SecurityCompletionMiddleware(app)(scope,None,send)
        assert len(calls)==(1 if failure=='capture' else 0) and scope['state']=={}
    asyncio.run(run())


def test_cache_bound_expiry_and_queue_reservation(monkeypatch):
    async def run():
        service=incident_producer.IncidentProducer(shared(settings()))
        monkeypatch.setattr(incident_producer,'_producer',service)
        now=time.time();actor=Actor(uuid4(),'admin');request_id=uuid4()
        service.security_seen.update({f'{i:064x}':now+1000 for i in range(1024)})
        descriptor={'success':(actor,'z'*64,now+1000)}
        security_producer.capture_security(descriptor,200,request_id)
        assert len(service.security_seen)==1024 and not service.queue.pending and service.discarded==1
        first=next(iter(service.security_seen));service.security_seen[first]=now-1
        security_producer.capture_security(descriptor,200,request_id)
        assert len(service.security_seen)==1024 and 'z'*64 in service.security_seen
        count=len(service.queue.pending);security_producer.capture_security(descriptor,200,request_id)
        assert len(service.queue.pending)==count
        service.security_seen.clear()
        monkeypatch.setattr(service.queue,'enqueue',lambda *args:False)
        security_producer.capture_security({'success':(actor,'q'*64,now+1000)},200,request_id)
        assert not service.security_seen
        await service.close();assert not service.security_seen
    asyncio.run(run())


@pytest.mark.integration
def test_real_api_security_and_regional_http_correlation(monkeypatch):
    from app.core.config import get_settings
    from app.main import app
    from app.db.session import engine
    from app.telemetry.schemas import TelemetryBatch
    from app.telemetry import router as telemetry_router
    from test_telemetry_shared import US
    config=get_settings()
    if config.database_url is None or not config.require_database_url().endswith('/telemetry_validation'):
        pytest.skip('Dedicated synthetic telemetry_validation database required')
    config=shared(config.model_copy(deep=True))
    for module in [incident_producer,security,telemetry_router]:monkeypatch.setattr(module,'get_settings',lambda:config)
    async def run():
        async with app.router.lifespan_context(app):
            service=incident_producer._producer;received=[]
            async def sink(body):
                batch=TelemetryBatch.model_validate_json(body);received.extend(e for e in batch.events if e.event_type != 'data_integrity_checked')
                return TelemetryReceipt(received=len(batch.events))
            service.queue.sink=sink
            async def drain():
                await asyncio.gather(*service.tasks)
                while service.queue.pending:await service.queue.flush()
            async with AsyncClient(transport=ASGITransport(app=app),base_url='http://test') as client:
                admin=uuid4();token=create_access_token(admin,'admin');headers={'Authorization':'Bearer '+token}
                ids={}
                for name in ['entryChannel','incidentType','severity']:
                    ids[name]=(await client.get('/catalogs/'+name,headers=headers)).json()['values'][0]['id']
                await drain();assert len(received)==1 and received[0].event_type=='authentication_succeeded'
                payload=dict(title='Synthetic security telemetry',description='Synthetic fixture',clinic_id=str(US),jurisdiction_id='00000000-0000-0000-0000-000000000001',affected_system_id='00000000-0000-0000-0000-000000000301',responsible_area_id='00000000-0000-0000-0000-000000000201',entry_channel_value_id=ids['entryChannel'],incident_type_value_id=ids['incidentType'],severity_value_id=ids['severity'])
                created=await client.post('/incidents',json=payload,headers=headers);assert created.status_code==201
                await drain();received.clear()
                new_token=create_access_token(uuid4(),'admin')
                result=await client.get('/incidents/'+created.json()['id'],headers={'Authorization':'Bearer '+new_token,'X-Request-Id':str(US)})
                assert result.status_code==200 and 'x-request-id' not in result.headers
                await drain();assert {e.event_type for e in received}=={'authentication_succeeded','api_request_completed'}
                assert len({e.requestId for e in received})==1
                by_type={e.event_type:e for e in received}
                assert by_type['authentication_succeeded'].properties.jurisdiction is None
                assert by_type['api_request_completed'].properties.jurisdiction=='US'
                assert by_type['authentication_succeeded'].userId!=by_type['api_request_completed'].userId
                received.clear()
                denied={'Authorization':'Bearer '+create_access_token(uuid4(),'direction')}
                assert (await client.get('/catalogs/severity',headers=denied)).status_code==403
                assert (await client.get('/catalogs/severity')).status_code==401
                await drain();assert {e.event_type for e in received}=={'authentication_succeeded','authorization_denied','authentication_failed'}
                received.clear()
                context=await client.post('/telemetry/context',json={'clinicId':None},headers={'Authorization':'Bearer '+create_access_token(uuid4(),'admin')})
                assert context.status_code==200
                await drain();assert not received
                assert token not in json.dumps(list(service.security_seen))
        await engine.dispose()
    asyncio.run(run())
