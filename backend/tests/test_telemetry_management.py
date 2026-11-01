import asyncio
import json
from contextlib import asynccontextmanager
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from app.auth.dependencies import Actor
from app.management.audit import ManagementAuditEvent
from app.management.service import add_audit_event
from app.telemetry import management_producer, incident_producer
from app.telemetry.schemas import TelemetryReceipt
from app.telemetry.server import ServerQueue
from test_telemetry_incident_producer import settings
from test_telemetry_shared import shared

US = UUID('00000000-0000-0000-0000-000000000001')
UK = UUID('00000000-0000-0000-0000-000000000002')


@pytest.mark.parametrize('action', ['created','updated','activated','deactivated'])
def test_persisted_snapshot_selects_historical_region(monkeypatch, action):
    actor=Actor(uuid4(),'admin');clinic=uuid4();audit_id=uuid4()
    audit=ManagementAuditEvent(id=audit_id,actor_id=actor.id,resource_type='clinics',resource_id=clinic,action=action,
                              before_data={'jurisdiction_id':str(US),'is_active':True},
                              after_data={'jurisdiction_id':str(UK),'is_active':False})
    class Session:
        async def get(self,model,identity): assert identity==audit_id;return audit
        async def scalar(self,statement):
            assert 'is_active' not in str(statement)
            identity=next(iter(statement.compile().params.values()))
            return {US:'US',UK:'UK'}[identity]
    @asynccontextmanager
    async def factory():yield Session()
    monkeypatch.setattr(management_producer.database,'SessionLocal',factory)
    result=asyncio.run(management_producer.resolve_audit(actor,audit_id))
    assert result==(clinic,'UK' if action=='created' else 'US',action)


@pytest.mark.parametrize('case',['missing','actor','resource','action','snapshot','unknown-region','denied'])
def test_invalid_audit_scope_never_falls_back(monkeypatch,case):
    actor=Actor(uuid4(),'technology' if case=='denied' else 'admin');audit_id=uuid4()
    audit=SimpleNamespace(actor_id=actor.id,resource_type='clinics',resource_id=uuid4(),action='updated',before_data={'jurisdiction_id':str(US)})
    if case=='actor':audit.actor_id=uuid4()
    if case=='resource':audit.resource_type='responsible-areas'
    if case=='action':audit.action='coverage_changed'
    if case=='snapshot':audit.before_data={}
    class Session:
        async def get(self,*args):return None if case=='missing' else audit
        async def scalar(self,*args):return 'ZZ'
    @asynccontextmanager
    async def factory():yield Session()
    monkeypatch.setattr(management_producer.database,'SessionLocal',factory)
    with pytest.raises(ValueError):asyncio.run(management_producer.resolve_audit(actor,audit_id))


@pytest.mark.parametrize('operation',['create','update','activate'])
@pytest.mark.parametrize('failure',[None,'commit','refresh'])
def test_management_hook_only_after_commit_and_before_refresh(monkeypatch,operation,failure):
    from app.management import router
    from app.management.schemas import ReferenceValueCreate,ReferenceValueUpdate,ActivationRequest
    from app.reference_data.models import Clinic
    actor=Actor(uuid4(),'admin');calls=[]
    clinic=Clinic(id=uuid4(),key='synthetic-clinic',label='Synthetic',jurisdiction_id=US,is_active=True)
    class Session:
        committed=False
        def __init__(self):self.added=[]
        def add(self,value):self.added.append(value)
        async def flush(self):
            for value in self.added:
                if value.id is None:value.id=uuid4()
        async def execute(self,*args):return SimpleNamespace(scalar_one_or_none=lambda:None)
        async def commit(self):
            if failure=='commit':raise RuntimeError('Synthetic rollback')
            self.committed=True
        async def refresh(self,value):
            assert len(calls)==1
            if failure=='refresh':raise RuntimeError('Synthetic refresh failure')
    session=Session()
    async def valid(*args):return clinic
    monkeypatch.setattr(router,'get_reference_or_404',valid)
    monkeypatch.setattr(router,'validate_active_jurisdiction',valid)
    def capture(observed_actor,audit_id):
        assert session.committed and observed_actor==actor
        audits=[v for v in session.added if isinstance(v,ManagementAuditEvent)]
        assert len(audits)==1 and audit_id==audits[0].id
        calls.append(audit_id)
    monkeypatch.setattr(router,'capture_management',capture)
    async def run():
        if operation=='create':await router.create_reference_value('clinics',ReferenceValueCreate(key='synthetic-created',label='Synthetic',jurisdiction_id=US),session,actor)
        elif operation=='update':await router.update_reference_value('clinics',clinic.id,ReferenceValueUpdate(label='Synthetic update'),session,actor)
        else:await router.set_reference_value_activation('clinics',clinic.id,ActivationRequest(is_active=False,reason='Synthetic validation'),session,actor)
    if failure:
        with pytest.raises(RuntimeError):asyncio.run(run())
    else:asyncio.run(run())
    assert len(calls)==(0 if failure=='commit' else 1)


def test_helper_return_and_patch_without_changes(monkeypatch):
    from app.management import router
    from app.management.schemas import ReferenceValueUpdate
    class Session:
        def __init__(self):self.added=[]
        def add(self,value):self.added.append(value)
    session=Session();actor=Actor(uuid4(),'admin')
    row=add_audit_event(session,resource_type='clinics',resource_id=uuid4(),action='updated',actor_id=actor.id,before_data={},after_data={})
    assert isinstance(row.id,UUID) and isinstance(row.correlation_id,UUID) and session.added==[row]
    async def value(*args):return SimpleNamespace(jurisdiction_id=US)
    monkeypatch.setattr(router,'get_reference_or_404',value)
    monkeypatch.setattr(router,'capture_management',lambda *args:pytest.fail('Empty PATCH must not capture'))
    asyncio.run(router.update_reference_value('clinics',uuid4(),ReferenceValueUpdate(),Session(),actor))


@pytest.mark.parametrize('failure',[None,'timeout','invalid'])
def test_shared_capture_private_and_bounded(monkeypatch,failure):
    async def run():
        gate=asyncio.Event();batches=[];actor=Actor(uuid4(),'admin');audit_id=uuid4();clinic=uuid4()
        async def resolve(*args):
            await gate.wait()
            if failure=='timeout':await asyncio.sleep(1)
            if failure=='invalid':raise ValueError('Synthetic invalid snapshot')
            return clinic,'US','deactivated'
        monkeypatch.setattr(management_producer,'resolve_audit',resolve)
        async def sink(body):
            batch=json.loads(body);batches.append(batch)
            return TelemetryReceipt(received=len(batch['events']))
        service=incident_producer.IncidentProducer(shared(settings()),queue=ServerQueue(sink=sink))
        monkeypatch.setattr(incident_producer,'_producer',service)
        for _ in range(16):assert management_producer.capture_management(actor,audit_id)
        assert not management_producer.capture_management(actor,audit_id)
        gate.set();await asyncio.gather(*service.tasks);await service.queue.flush()
        if failure:assert not batches and service.discarded==17
        else:
            event=batches[0]['events'][0]
            assert set(event['properties'])=={'jurisdiction','environment','auditId','resource','action'}
            assert event['properties']['action']=='deactivated' and event['properties']['resource']=='reference'
            assert event['properties']['auditId']==incident_producer.resource_id(incident_producer.region_settings(service.settings,'US'),'audit',audit_id)
            text=json.dumps(batches);assert all(str(i) not in text for i in [actor.id,clinic,audit_id])
        await service.close();assert not service.tasks
    asyncio.run(run())


@pytest.mark.integration
def test_real_management_mutations_historical_region_and_rollback(monkeypatch):
    from httpx import AsyncClient,ASGITransport
    from sqlalchemy import event,select
    from sqlalchemy.orm import Session
    from app.core.config import get_settings
    from app.main import app
    from app.auth import security
    from app.auth.security import create_access_token
    from app.db.session import SessionLocal,engine
    from app.telemetry.schemas import TelemetryBatch
    from app.reference_data.models import Clinic
    from app.telemetry.context import resolve_clinic
    from fastapi import HTTPException
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
            actor=Actor(uuid4(),'admin');headers={'Authorization':'Bearer '+create_access_token(actor.id,actor.role)}
            async with AsyncClient(transport=ASGITransport(app=app,raise_app_exceptions=False),base_url='http://test') as client:
                payload=dict(key='synthetic-tel-'+uuid4().hex[:12],label='Synthetic management telemetry',jurisdiction_id=str(US))
                created=await client.post('/management/reference-data/clinics',json=payload,headers=headers)
                assert created.status_code==201;clinic_id=UUID(created.json()['id']);await drain()
                assert len(received)==1 and received[-1].properties.action=='created' and received[-1].properties.jurisdiction=='US'
                url='/management/reference-data/clinics/'+str(clinic_id)
                response=await client.patch(url,json={'jurisdiction_id':str(UK)},headers=headers);assert response.status_code==200
                await drain();assert received[-1].properties.jurisdiction=='US' and received[-1].properties.action=='updated'
                for active,action in [(False,'deactivated'),(True,'activated')]:
                    assert (await client.post(url+'/activation',json={'is_active':active,'reason':'Synthetic validation'},headers=headers)).status_code==200
                    await drain();assert received[-1].properties.jurisdiction=='UK' and received[-1].properties.action==action
                    if not active:
                        with pytest.raises(HTTPException):await resolve_clinic(config,actor,clinic_id=clinic_id)
                assert len(received)==4
                assert (await client.patch(url,json={},headers=headers)).status_code==200
                assert (await client.post('/management/reference-data/clinics',json=payload,headers=headers)).status_code==409
                denied={'Authorization':'Bearer '+create_access_token(uuid4(),'technology')}
                assert (await client.patch(url,json={'label':'Synthetic denied'},headers=denied)).status_code==403
                await drain();assert len(received)==4
                def fail(session):raise RuntimeError('Synthetic commit failure')
                event.listen(Session,'before_commit',fail)
                try:assert (await client.patch(url,json={'label':'Synthetic rollback'},headers=headers)).status_code==500
                finally:event.remove(Session,'before_commit',fail)
                await drain();assert len(received)==4
                async with SessionLocal() as session:
                    audits=(await session.execute(select(ManagementAuditEvent).where(ManagementAuditEvent.resource_id==clinic_id))).scalars().all()
                    assert len(audits)==4
                    clinic=await session.get(Clinic,clinic_id);assert clinic.label==payload['label'] and clinic.jurisdiction_id==UK
                    for row,emitted in zip(sorted(audits,key=lambda row:row.occurred_at),received):
                        scoped=incident_producer.region_settings(config,emitted.properties.jurisdiction)
                        assert emitted.properties.auditId==incident_producer.resource_id(scoped,'audit',row.id)
                assert str(clinic_id) not in json.dumps([e.model_dump() for e in received])
                async def broken(body):raise RuntimeError('Synthetic sink failure')
                service.queue.sink=broken
                assert (await client.patch(url,json={'label':'Synthetic successful update'},headers=headers)).status_code==200
                await drain();assert len(received)==4
        await engine.dispose()
    asyncio.run(run())
