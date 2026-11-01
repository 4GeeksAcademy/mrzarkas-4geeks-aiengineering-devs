import asyncio
import json
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import SecretStr
from fastapi import HTTPException

from app.core.config import Settings
from app.auth.dependencies import Actor
from app.telemetry import incident_producer as producer
from app.telemetry.server import ServerQueue
from app.telemetry.schemas import TelemetryReceipt


def settings():
    return Settings(_env_file=None,app_environment='test',database_url=None,telemetry_enabled=True,
                    telemetry_processing_region='US',telemetry_user_key=SecretStr('u'*32),
                    telemetry_subject_key=SecretStr('s'*32),telemetry_clinic_key=SecretStr('c'*32),
                    telemetry_context_key=SecretStr('t'*32),telemetry_resource_key=SecretStr('r'*32))


def test_resource_key_separation_and_fail_closed():
    config=settings();identity=uuid4()
    first=producer.resource_id(config,'incident',identity)
    assert first==producer.resource_id(config,'incident',identity)
    assert first!=producer.resource_id(config,'audit',identity)
    config.telemetry_resource_key=SecretStr('k'*32)
    assert first!=producer.resource_id(config,'incident',identity)
    for value in [None,'short','u'*32,'s'*32,'c'*32,'t'*32,config.jwt_secret_key.get_secret_value()]:
        config.telemetry_resource_key=None if value is None else SecretStr(value)
        with pytest.raises(producer.ConfigurationError):producer.resource_key(config)


def test_capture_is_async_bounded_and_exports_only_opaque_fields(monkeypatch):
    async def run():
        batches=[];gate=asyncio.Event();actor=Actor(uuid4(),'technology');ids=[uuid4() for _ in range(3)]
        async def resolve(*args,**kwargs):await gate.wait();return 'opaque-clinic','US'
        monkeypatch.setattr(producer,'resolve_clinic',resolve)
        async def sink(body):batches.append(json.loads(body));return TelemetryReceipt(received=len(batches[-1]['events']))
        service=producer.IncidentProducer(settings(),queue=ServerQueue(sink=sink))
        for _ in range(16):assert service.capture('incident_created',actor,*ids)
        assert not service.capture('incident_created',actor,*ids) and len(service.tasks)==16
        gate.set();await asyncio.gather(*service.tasks);await service.queue.flush()
        text=json.dumps(batches)
        assert all(str(identity) not in text for identity in [actor.id,*ids])
        event=batches[0]['events'][0]
        assert event['sessionId'] is None and event['requestId'] is None
        assert set(event['properties'])=={'jurisdiction','environment','incidentId','auditId'}
        assert event['userId'].startswith('ps_') and event['properties']['jurisdiction']=='US'
        await service.close();assert not service.tasks and service.queue.closed
    asyncio.run(run())


@pytest.mark.parametrize('failure',['inactive','timeout','unexpected'])
def test_resolution_failure_discards_without_general_fallback(monkeypatch,failure):
    async def run():
        async def resolve(*args,**kwargs):
            if failure=='timeout':await asyncio.sleep(1)
            elif failure=='inactive':raise HTTPException(422,'Invalid clinic context')
            else:raise RuntimeError('synthetic-sensitive')
        monkeypatch.setattr(producer,'resolve_clinic',resolve)
        service=producer.IncidentProducer(settings())
        assert service.capture('incident_created',Actor(uuid4(),'technology'),uuid4(),uuid4(),uuid4())
        await asyncio.gather(*service.tasks)
        assert service.discarded==1 and not service.queue.pending
        await service.close()
    asyncio.run(run())


def test_optional_lifecycle_and_capture_failure_do_not_escape(monkeypatch):
    monkeypatch.setattr(producer,'get_settings',lambda:Settings(_env_file=None))
    assert producer.start() is None
    producer.capture_incident('incident_created',None,None,None,None)
    class Broken:
        def capture(self,*args):raise RuntimeError('synthetic-sensitive')
    monkeypatch.setattr(producer,'_producer',Broken())
    producer.capture_incident('incident_created',None,None,None,None)


@pytest.mark.parametrize('operation',['create','transition','assign'])
@pytest.mark.parametrize('failure',[None,'commit','refresh'])
def test_incident_hooks_only_after_commit_and_before_refresh(monkeypatch,operation,failure):
    from app.incidents import router
    from app.incidents.models import OperationalIncident
    from app.incidents.history import AuditEvent
    from app.incidents.schemas import IncidentCreate,IncidentAssignmentRequest,StatusTransitionRequest
    actor=Actor(uuid4(),'admin');events=[];target=SimpleNamespace(id=uuid4(),key='underAnalysis')
    current=SimpleNamespace(id=uuid4(),key='new')
    incident=OperationalIncident(id=uuid4(),clinic_id=uuid4(),jurisdiction_id=uuid4(),responsible_area_id=uuid4(),status_value_id=current.id)
    class Session:
        committed=False
        def __init__(self):self.added=[]
        def add(self,value):self.added.append(value)
        async def get(self,model,identity):return incident if model is OperationalIncident else current
        async def flush(self):
            for value in self.added:
                if value.id is None:value.id=uuid4()
        async def execute(self,statement):return SimpleNamespace(scalar_one_or_none=lambda:current)
        async def commit(self):
            if failure=='commit':raise RuntimeError('commit failed')
            await self.flush();self.committed=True
        async def refresh(self,value):
            assert len(events)==1
            if failure=='refresh':raise RuntimeError('refresh failed')
    session=Session()
    async def valid(*args):pass
    async def catalog(*args):return target
    monkeypatch.setattr(router,'validate_incident_references',valid)
    monkeypatch.setattr(router,'validate_responsible_area',valid)
    monkeypatch.setattr(router,'get_catalog_value',catalog)
    def capture(kind,observed_actor,clinic,identity,audit):
        assert session.committed and observed_actor==actor
        stored=[value for value in session.added if isinstance(value,AuditEvent)]
        assert len(stored)==1 and audit==stored[0].id
        events.append(kind)
    monkeypatch.setattr(router,'capture_incident',capture)
    async def run():
        if operation=='create':
            payload=IncidentCreate(title='Synthetic',description='Synthetic fixture',clinic_id=uuid4(),jurisdiction_id=uuid4(),affected_system_id=uuid4(),responsible_area_id=uuid4(),entry_channel_value_id=uuid4(),incident_type_value_id=uuid4(),severity_value_id=uuid4())
            await router.create_incident(payload,session,actor)
        elif operation=='transition':await router.transition_incident(incident.id,StatusTransitionRequest(status_value_id=target.id),session,actor)
        else:await router.assign_incident(incident.id,IncidentAssignmentRequest(responsible_area_id=uuid4()),session,actor)
    if failure:
        with pytest.raises(RuntimeError):asyncio.run(run())
    else:asyncio.run(run())
    assert events==([] if failure=='commit' else [{'create':'incident_created','transition':'incident_transitioned','assign':'incident_assigned'}[operation]])


@pytest.mark.integration
def test_real_postcommit_rollback_and_audit_links():
    from httpx import AsyncClient, ASGITransport
    from sqlalchemy import select, func, event
    from sqlalchemy.orm import Session
    from app.core.config import get_settings
    from app.main import app
    from app.db.session import SessionLocal, engine
    from app.incidents.models import OperationalIncident
    from app.incidents.history import AuditEvent
    from app.auth.security import create_access_token
    from app.telemetry import incident_producer
    from app.telemetry.schemas import TelemetryBatch
    from uuid import UUID
    config = get_settings()
    if config.database_url is None or not config.require_database_url().endswith('/telemetry_validation'):
        pytest.skip('Dedicated telemetry_validation database with synthetic seeds required')
    async def main():
     async with app.router.lifespan_context(app):
      producer=incident_producer._producer;assert producer is not None
      received=[]
      async def sink(body):
       data=TelemetryBatch.model_validate_json(body);received.extend(e for e in data.events if e.event_type not in {'authentication_succeeded', 'authentication_failed', 'authorization_denied', 'service_health_checked', 'catalog_cache_observed', 'data_integrity_checked'});return TelemetryReceipt(received=len(data.events))
      producer.queue.sink=sink
      async def drain():
       await asyncio.gather(*producer.tasks)
       while producer.queue.pending:await producer.queue.flush()
      headers={'Authorization':'Bearer '+create_access_token(UUID('00000000-0000-4000-8000-000000000001'),'admin')}
      async with AsyncClient(transport=ASGITransport(app=app,raise_app_exceptions=False),base_url='http://test') as client:
       ids={}
       for name in ['entryChannel','incidentType','severity','incidentStatus']:
        response=await client.get('/catalogs/'+name,headers=headers)
        ids[name]={v['key']:v['id'] for v in response.json()['values']}
       payload=dict(title='Synthetic business telemetry',description='Synthetic fixture without patient data',clinic_id='00000000-0000-0000-0000-000000000101',jurisdiction_id='00000000-0000-0000-0000-000000000001',affected_system_id='00000000-0000-0000-0000-000000000301',responsible_area_id='00000000-0000-0000-0000-000000000201',entry_channel_value_id=next(iter(ids['entryChannel'].values())),incident_type_value_id=next(iter(ids['incidentType'].values())),severity_value_id=next(iter(ids['severity'].values())))
       response=await client.post('/incidents',json=payload,headers=headers);assert response.status_code==201,response.text
       identity=response.json()['id'];await drain();assert len(received)==1
       transition={'status_value_id':ids['incidentStatus']['underAnalysis']}
       assert (await client.post('/incidents/'+identity+'/transitions',json=transition,headers=headers)).status_code==200
       await drain();assert len(received)==2
       assignment={'responsible_area_id':'00000000-0000-0000-0000-000000000202'}
       assert (await client.post('/incidents/'+identity+'/assignments',json=assignment,headers=headers)).status_code==200
       await drain();assert len(received)==3
       assert (await client.post('/incidents/'+identity+'/transitions',json=transition,headers=headers)).status_code==409
       assert (await client.post('/incidents/'+identity+'/assignments',json=assignment,headers=headers)).status_code==409
       denied={'Authorization':'Bearer '+create_access_token(UUID('00000000-0000-4000-8000-000000000002'),'direction')}
       assert (await client.post('/incidents',json=payload,headers=denied)).status_code==403
       await drain();assert len(received)==3
       async def counts():
        async with SessionLocal() as db:return [await db.scalar(select(func.count()).select_from(model)) for model in [OperationalIncident,AuditEvent]]
       before=await counts()
       def fail(session):raise RuntimeError('Synthetic commit failure')
       event.listen(Session,'before_commit',fail)
       try:assert (await client.post('/incidents',json=payload,headers=headers)).status_code==500
       finally:event.remove(Session,'before_commit',fail)
       await drain();assert len(received)==3 and await counts()==before
       async with SessionLocal() as db:
        audits=(await db.execute(select(AuditEvent).where(AuditEvent.entity_id==UUID(identity)))).scalars().all()
        assert len(audits)==3
        expected={incident_producer.resource_id(producer.settings,'audit',row.id) for row in audits}
        assert {e.properties.auditId for e in received}==expected
       assert {e.event_type for e in received}=={'incident_created','incident_transitioned','incident_assigned'}
       assert all(e.properties.jurisdiction=='US' and e.sessionId is None and e.requestId is None for e in received)
       exported=json.dumps([e.model_dump() for e in received])
       assert identity not in exported and payload['title'] not in exported and payload['clinic_id'] not in exported
       async def broken(body):raise RuntimeError('Synthetic sink error')
       producer.queue.sink=broken
       assert (await client.post('/incidents',json=payload,headers=headers)).status_code==201
       await drain();assert producer.queue.counts['discarded']==1
       print(json.dumps({'status':'PASS','events':[e.event_type for e in received],'rollback_no_event':True,'conflict_denied_no_event':True,'durable_audit_preserved':True,'sink_failure_business_success':True,'raw_identifiers_exported':False}))
     await engine.dispose()
    asyncio.run(main())
