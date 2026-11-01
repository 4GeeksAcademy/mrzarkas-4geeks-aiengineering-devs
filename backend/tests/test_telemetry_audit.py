import asyncio
import json
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.auth.dependencies import Actor
from app.telemetry import audit_producer, incident_producer
from app.telemetry.audit_completion import AuditCompletionMiddleware
from app.telemetry.schemas import TelemetryReceipt
from app.telemetry.server import ServerQueue
from test_telemetry_incident_producer import settings


@pytest.mark.parametrize('status', [200, 201, 204, 400, 401, 403, 404, 422, 500])
def test_capture_only_after_successful_final_body(monkeypatch, status):
    async def run():
        calls, sent = [], []
        actor, clinic = Actor(uuid4(), 'admin'), uuid4()
        monkeypatch.setattr('app.telemetry.audit_completion.capture_audit', lambda *args: calls.append(args))
        async def application(scope, receive, send):
            scope['state'][audit_producer.STATE_KEY] = (actor, clinic, 'incident')
            await send({'type': 'http.response.start', 'status': status, 'headers': []})
            await send({'type': 'http.response.body', 'body': b'[', 'more_body': True})
            assert not calls
            await send({'type': 'http.response.body', 'body': b']', 'more_body': False})
        async def send(message):
            assert not calls
            sent.append(message.copy())
        scope = {'type': 'http'}
        await AuditCompletionMiddleware(application)(scope, None, send)
        assert calls == ([(actor, clinic, 'incident')] if status < 300 else [])
        assert [m.get('body') for m in sent[1:]] == [b'[', b']']
        assert audit_producer.STATE_KEY not in scope['state']
    asyncio.run(run())


@pytest.mark.parametrize('failure', ['query', 'serialization', 'send', 'cancel'])
def test_failures_never_capture_and_preserve_exception(monkeypatch, failure):
    async def run():
        calls = []
        monkeypatch.setattr('app.telemetry.audit_completion.capture_audit', lambda *args: calls.append(args))
        async def application(scope, receive, send):
            if failure == 'query': raise RuntimeError('synthetic SQL failure')
            scope['state'][audit_producer.STATE_KEY] = (Actor(uuid4(), 'admin'), uuid4(), 'incident')
            if failure == 'serialization': raise RuntimeError('synthetic serialization failure')
            await send({'type': 'http.response.start', 'status': 200, 'headers': []})
            await send({'type': 'http.response.body', 'body': b'[]'})
        async def send(message):
            if message['type'] == 'http.response.body':
                if failure == 'cancel': raise asyncio.CancelledError()
                raise OSError('synthetic disconnected client')
        expected = asyncio.CancelledError if failure == 'cancel' else (OSError if failure == 'send' else RuntimeError)
        scope = {'type': 'http'}
        with pytest.raises(expected): await AuditCompletionMiddleware(application)(scope, None, send)
        assert not calls and audit_producer.STATE_KEY not in scope['state']
    asyncio.run(run())


def test_missing_descriptor_non_http_and_broken_capture_are_isolated(monkeypatch):
    async def run():
        calls = []
        def broken(*args): calls.append(args); raise RuntimeError('synthetic telemetry error')
        monkeypatch.setattr('app.telemetry.audit_completion.capture_audit', broken)
        async def application(scope, receive, send):
            if scope['type'] != 'http': return
            if scope.get('mark'):
                scope['state'][audit_producer.STATE_KEY] = (Actor(uuid4(), 'admin'), uuid4(), 'incident')
            await send({'type':'http.response.start','status':200,'headers':[]})
            await send({'type':'http.response.body','body':b'[]'})
        async def send(message): pass
        middleware=AuditCompletionMiddleware(application)
        await middleware({'type':'http'},None,send)
        await middleware({'type':'lifespan'},None,send)
        assert not calls
        await middleware({'type':'http','mark':True},None,send)
        assert len(calls)==1
    asyncio.run(run())


@pytest.mark.parametrize('failure', [None, 'inactive', 'timeout'])
def test_audit_capture_bounded_private_and_resolution_fail_closed(monkeypatch, failure):
    async def run():
        gate=asyncio.Event(); batches=[]
        async def resolver(*args, **kwargs):
            await gate.wait()
            if failure=='inactive': raise HTTPException(422,'Inactive clinic')
            if failure=='timeout': await asyncio.sleep(1)
            return 'opaque-clinic','US'
        monkeypatch.setattr(audit_producer,'resolve_clinic',resolver)
        async def sink(body):
            batch=json.loads(body);batches.append(batch)
            return TelemetryReceipt(received=len(batch['events']))
        service=incident_producer.IncidentProducer(settings(),queue=ServerQueue(sink=sink))
        monkeypatch.setattr(incident_producer,'_producer',service)
        actor,clinic=Actor(uuid4(),'admin'),uuid4()
        for _ in range(16): assert audit_producer.capture_audit(actor,clinic,'incident')
        assert not audit_producer.capture_audit(actor,clinic,'management')
        assert len(service.tasks)==16
        gate.set();await asyncio.gather(*service.tasks);await service.queue.flush()
        if failure: assert not batches and service.discarded==17
        else:
            assert len(batches[0]['events'])==16
            event=batches[0]['events'][0]
            assert set(event['properties'])=={'jurisdiction','environment','surface'}
            assert event['requestId'] is None and event['sessionId'] is None
            assert str(actor.id) not in json.dumps(batches) and str(clinic) not in json.dumps(batches)
        await service.close();assert not service.tasks and service.queue.closed
        assert not audit_producer.capture_audit(actor,clinic,'incident')
    asyncio.run(run())


@pytest.mark.integration
def test_real_audit_reads_both_surfaces_and_denials(monkeypatch):
    from app.core.config import get_settings
    from app.main import app
    from app.telemetry import router as telemetry_router
    from app.auth import security
    from app.auth.security import create_access_token
    from app.db.session import engine
    from httpx import AsyncClient, ASGITransport
    from app.telemetry.schemas import TelemetryBatch
    from test_telemetry_shared import shared, US, UK
    config=get_settings()
    if config.database_url is None or not config.require_database_url().endswith('/telemetry_validation'):
        pytest.skip('Dedicated synthetic telemetry_validation database required')
    config=shared(config.model_copy(deep=True))
    for module in [incident_producer,telemetry_router,security]: monkeypatch.setattr(module,'get_settings',lambda:config)
    async def run():
        async with app.router.lifespan_context(app):
            service=incident_producer._producer; assert service is not None
            received=[]
            async def sink(body):
                batch=TelemetryBatch.model_validate_json(body);received.extend(e for e in batch.events if e.event_type not in {'api_request_completed', 'authentication_succeeded', 'authentication_failed', 'authorization_denied', 'service_health_checked', 'catalog_cache_observed', 'data_integrity_checked'})
                return TelemetryReceipt(received=len(batch.events))
            service.queue.sink=sink
            async def drain():
                await asyncio.gather(*service.tasks)
                while service.queue.pending: await service.queue.flush()
            headers={'Authorization':'Bearer '+create_access_token(uuid4(),'admin')}
            async with AsyncClient(transport=ASGITransport(app=app),base_url='http://test') as client:
                ids={}
                for name in ['entryChannel','incidentType','severity']:
                    result=await client.get('/catalogs/'+name,headers=headers)
                    ids[name]=result.json()['values'][0]['id']
                for clinic,jurisdiction,system in [(US,'00000000-0000-0000-0000-000000000001','00000000-0000-0000-0000-000000000301'),(UK,'00000000-0000-0000-0000-000000000002','00000000-0000-0000-0000-000000000304')]:
                    payload=dict(title='Synthetic audit telemetry',description='Synthetic fixture without patient data',clinic_id=str(clinic),jurisdiction_id=jurisdiction,affected_system_id=system,responsible_area_id='00000000-0000-0000-0000-000000000201',entry_channel_value_id=ids['entryChannel'],incident_type_value_id=ids['incidentType'],severity_value_id=ids['severity'])
                    created=await client.post('/incidents',json=payload,headers=headers);assert created.status_code==201
                    await drain();received.clear()
                    response=await client.get('/incidents/'+created.json()['id']+'/audit',headers=headers)
                    assert response.status_code==200 and len(response.json())==1
                    await drain();assert len(received)==1
                    assert received[0].event_type=='audit_accessed' and received[0].properties.surface=='incident'
                    region='US' if clinic==US else 'UK';assert received[0].properties.jurisdiction==region
                    response=await client.get('/management/audit-events',params={'resource_type':'clinics','resource_id':str(clinic)},headers=headers)
                    assert response.status_code==200
                    await drain();assert len(received)==2 and received[-1].properties.surface=='management'
                    assert received[-1].properties.jurisdiction==region
                    for params in [{},{'resource_type':'clinics'},{'resource_type':'responsible-areas','resource_id':str(clinic)},{'resource_type':'clinics','resource_id':str(uuid4())}]:
                        assert (await client.get('/management/audit-events',params=params,headers=headers)).status_code==200
                    assert (await client.get('/incidents/'+str(uuid4())+'/audit',headers=headers)).status_code==404
                    denied={'Authorization':'Bearer '+create_access_token(uuid4(),'direction')}
                    assert (await client.get('/incidents/'+created.json()['id']+'/audit',headers=denied)).status_code==403
                    await drain();assert len(received)==2
                    assert str(clinic) not in json.dumps([e.model_dump() for e in received])
                    async def broken(body): raise RuntimeError('Synthetic sink failure')
                    service.queue.sink=broken
                    assert (await client.get('/incidents/'+created.json()['id']+'/audit',headers=headers)).status_code==200
                    await drain();assert len(received)==2
                    service.queue.sink=sink
        await engine.dispose()
    asyncio.run(run())
