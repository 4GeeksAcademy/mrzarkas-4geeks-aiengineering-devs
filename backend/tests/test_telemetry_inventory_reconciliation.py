"""Independent reconstruction, read-only snapshots and genuine checker mismatch."""
import asyncio
import json
from types import SimpleNamespace
from uuid import uuid4
import pytest
from app.auth.dependencies import Actor
from app.inventory import reconciliation as checker
from app.telemetry import inventory_reconciliation_producer as producer, incident_producer
from app.telemetry.server import ServerQueue
from app.telemetry.schemas import TelemetryReceipt
from test_telemetry_incident_producer import settings
from test_telemetry_shared import shared
from test_telemetry_context import telemetry

@pytest.mark.parametrize('case',['match','mismatch','zero','lot','legacy','foreign','limit'])
def test_independent_sum(case,monkeypatch):
    country,lot=uuid4(),uuid4()
    rows=[SimpleNamespace(delta=3,lot_id=lot,jurisdiction_id=country,jurisdiction_key='US'),
          SimpleNamespace(delta=-1,lot_id=None,jurisdiction_id=country,jurisdiction_key='US')]
    value=2
    if case=='mismatch': value=4
    if case=='zero': rows=[];value=0
    if case=='lot': value=3
    if case=='legacy': rows[0].jurisdiction_id=None
    if case=='foreign': rows[0].jurisdiction_key='UK'
    if case=='limit': monkeypatch.setattr(checker,'LIMIT',1)
    expected='inconclusive' if case in {'legacy','foreign','limit'} else 'mismatched' if case=='mismatch' else 'matched'
    assert checker.compare(SimpleNamespace(quantity=value),rows,country,'US',lot if case=='lot' else None)==expected


@pytest.mark.integration
@pytest.mark.parametrize('region',['US','UK'])
def test_readonly_reconciliation_http_snapshot_and_minimal_event(monkeypatch,region):
    from sqlalchemy import select,func,text
    from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
    from httpx import ASGITransport,AsyncClient
    from app.reference_data import seed
    from app.reference_data.models import Jurisdiction
    from app.inventory import service
    from app.inventory.models import InventoryMovement,InventoryAudit,InventoryItem
    from app.inventory.schemas import ItemCreate,ClinicConfig,LotCreate,MovementCreate
    from app.auth.security import create_access_token
    from app.db.session import get_session
    from app.main import app
    from test_inventory import isolated_url,setup_fixture
    async def run():
        engine=create_async_engine(isolated_url());factory=async_sessionmaker(engine,expire_on_commit=False)
        monkeypatch.setattr(checker.database,'engine',engine)
        monkeypatch.setattr(producer.database,'SessionLocal',factory)
        monkeypatch.setattr(seed,'SessionLocal',factory)
        await seed.seed_reference_data()
        async with factory() as session,session.begin():
            c1,c2,admin,_,_=await setup_fixture(session)
            clinic=c1 if region=='US' else c2
            country=await session.scalar(select(Jurisdiction).where(Jurisdiction.key==region));clinic.jurisdiction_id=country.id
            manager=Actor(uuid4(),'inventoryManager',clinic_ids=(clinic.id,))
            auditor=Actor(uuid4(),'inventoryAuditor',jurisdiction_ids=(country.id,))
            item=await service.create_item(session,admin,ItemCreate(title='Synthetic reconciliation',product_code='SYN-REC-'+str(uuid4()),unit='piece',uses_lots=True))
            await service.configure(session,manager,item.id,clinic.id,ClinicConfig(reorder_point=2))
            lots=[await service.create_lot(session,admin,item.id,LotCreate(code='L'+str(i))) for i in range(2)]
            for lot in lots: await service.movement(session,manager,MovementCreate(item_id=item.id,clinic_id=clinic.id,lot_id=lot.id,kind='in',quantity=3))
            out=await service.movement(session,manager,MovementCreate(item_id=item.id,clinic_id=clinic.id,lot_id=lots[0].id,kind='out',quantity=1))
            await service.movement(session,manager,MovementCreate(item_id=item.id,clinic_id=clinic.id,lot_id=lots[1].id,kind='adjust',counted_quantity=5,reason='synthetic count'))
            await service.correct(session,manager,out.id,'synthetic correction')
        async def counts():
            async with factory() as session:
                return tuple([await session.scalar(select(func.count()).select_from(m).where(m.item_id==item.id)) for m in [InventoryMovement,InventoryAudit]])
        before=await counts();events=[]
        async def sink(body):
            batch=json.loads(body);events.extend(batch['events']);return TelemetryReceipt(received=len(batch['events']))
        telemetry_service=incident_producer.IncidentProducer(shared(settings()),queue=ServerQueue(sink=sink))
        monkeypatch.setattr(incident_producer,'_producer',telemetry_service)
        async def sessions():
            async with factory() as session: yield session
        old=app.dependency_overrides.get(get_session);app.dependency_overrides[get_session]=sessions
        original=checker.service.stock
        try:
            assert (await checker.check(auditor,item.id,clinic.id)).result=='matched'
            assert (await checker.check(auditor,item.id,clinic.id,lots[0].id)).result=='matched'
            path=f'/inventory/items/{item.id}/clinics/{clinic.id}/reconciliation'
            headers={'Authorization':'Bearer '+create_access_token(auditor.id,auditor.role,jurisdiction_ids=auditor.jurisdiction_ids)}
            async with AsyncClient(transport=ASGITransport(app=app),base_url='http://test') as client:
                response=await client.post(path,headers=headers)
                assert response.status_code==200 and response.json()=={'result':'matched','telemetryAccepted':False}
                assert (await client.post(path)).status_code==401
                assert (await client.post(path,headers=headers,json={'stock':1})).status_code==422
                denied={'Authorization':'Bearer '+create_access_token(manager.id,manager.role,clinic_ids=manager.clinic_ids)}
                assert (await client.post(path,headers=denied)).status_code==403
                async def wrong(*args):
                    value=await original(*args);return value.model_copy(update={'quantity':value.quantity+1})
                monkeypatch.setattr(checker.service,'stock',wrong)
                response=await client.post(path,headers=headers)
                assert response.status_code==200 and response.json()=={'result':'mismatched','telemetryAccepted':True}
                await asyncio.gather(*telemetry_service.tasks)
                while telemetry_service.queue.pending: await telemetry_service.queue.flush()
                failures=[e for e in events if e['event_type']=='inventory_reconciliation_failed']
                assert len(failures)==1
                assert set(failures[0]['properties'])=={'jurisdiction','environment','checkId','check'}
                assert failures[0]['properties']['jurisdiction']==region and failures[0]['properties']['check']=='stock_projection'
                assert str(item.id) not in json.dumps(failures) and str(auditor.id) not in json.dumps(failures)
            monkeypatch.setattr(checker.service,'stock',original)
            assert await counts()==before
            async def forbidden_write(session,*args):
                await session.execute(text('UPDATE inventory_item SET pack_size=2 WHERE id=:id'),{'id':item.id})
            monkeypatch.setattr(checker.service,'stock',forbidden_write)
            assert (await checker.check(auditor,item.id,clinic.id)).result=='inconclusive'
            monkeypatch.setattr(checker.service,'stock',original)
            assert await counts()==before
            async with factory() as observer:
                assert (await observer.get(InventoryItem,item.id)).pack_size == 1
            async def concurrent(session,*args):
                assert await session.scalar(text('SHOW transaction_isolation')) == 'repeatable read'
                assert await session.scalar(text('SHOW transaction_read_only')) == 'on'
                projected=await original(session,*args)
                async with factory() as writer,writer.begin():
                    await service.movement(writer,manager,MovementCreate(item_id=item.id,clinic_id=clinic.id,lot_id=lots[0].id,kind='in',quantity=2))
                return projected
            monkeypatch.setattr(checker.service,'stock',concurrent)
            assert (await checker.check(auditor,item.id,clinic.id)).result=='matched'
            monkeypatch.setattr(checker.service,'stock',original)
            monkeypatch.setattr(checker,'LIMIT',1)
            assert (await checker.check(auditor,item.id,clinic.id)).result=='inconclusive'
        finally:
            if old is None: app.dependency_overrides.pop(get_session,None)
            else: app.dependency_overrides[get_session]=old
            await telemetry_service.close();await engine.dispose()
    asyncio.run(run())


def test_browser_rejects_reconciliation(telemetry):
    from datetime import UTC,datetime
    _,request=telemetry
    context=request('/telemetry/context',{'clinicId':None}).json()
    event=dict(eventId=str(uuid4()),timestamp=datetime.now(UTC).isoformat(),schemaVersion='1.3.0',sessionId=context['sessionId'],userId=context['userId'],requestId=None,event_type='inventory_reconciliation_failed',properties=dict(jurisdiction='US',environment='test',checkId='ps_'+'a'*64,check='stock_projection'))
    assert request('/telemetry/events',{'events':[event]},headers={'X-Telemetry-Context':context['contextToken']}).status_code==403

@pytest.mark.parametrize('case',['valid','role','scope','item','inactive-item','clinic','inactive-clinic','country','inactive-country','region'])
def test_producer_revalidates_context(monkeypatch,case):
    from contextlib import asynccontextmanager
    from fastapi import HTTPException
    from app.inventory.models import InventoryItem
    from app.reference_data.models import Clinic,Jurisdiction
    clinic,country,item=uuid4(),uuid4(),uuid4()
    actor=Actor(uuid4(),'inventoryManager' if case=='role' else 'inventoryAuditor',jurisdiction_ids=() if case=='scope' else (country,))
    class Session:
        async def get(self,model,value):
            return {InventoryItem:None if case=='item' else SimpleNamespace(is_active=case!='inactive-item'),
                Clinic:None if case=='clinic' else SimpleNamespace(id=clinic,jurisdiction_id=country,is_active=case!='inactive-clinic'),
                Jurisdiction:None if case=='country' else SimpleNamespace(key='UK' if case=='region' else 'US',is_active=case!='inactive-country')}[model]
    @asynccontextmanager
    async def factory(): yield Session()
    monkeypatch.setattr(producer.database,'SessionLocal',factory)
    if case=='valid': assert asyncio.run(producer.resolve_attempt(actor,item,clinic,'US'))=='US'
    else:
        with pytest.raises((HTTPException,ValueError)): asyncio.run(producer.resolve_attempt(actor,item,clinic,'US'))


def test_timeout_is_inconclusive(monkeypatch):
    async def slow(*args): await asyncio.sleep(2)
    monkeypatch.setattr(checker,'_check',slow)
    assert asyncio.run(checker.check(Actor(uuid4(),'inventoryAuditor'),uuid4(),uuid4())).result=='inconclusive'


def test_optional_producer_failures(monkeypatch):
    monkeypatch.setattr(incident_producer,'_producer',None)
    assert not producer.capture_reconciliation(None,None,None,None,None)
    async def run():
        tracked=incident_producer.IncidentProducer(shared(settings()))
        monkeypatch.setattr(incident_producer,'_producer',tracked)
        actor=Actor(uuid4(),'inventoryAuditor')
        assert not producer.capture_reconciliation(actor,uuid4(),uuid4(),'other',uuid4())
        tracked.tasks=set(range(16))
        assert not producer.capture_reconciliation(actor,uuid4(),uuid4(),'US',uuid4())
        tracked.tasks.clear()
        async def unavailable(*args): raise ValueError('synthetic')
        monkeypatch.setattr(producer,'resolve_attempt',unavailable)
        assert producer.capture_reconciliation(actor,uuid4(),uuid4(),'US',uuid4())
        await asyncio.gather(*tracked.tasks)
        assert not tracked.queue.pending
        await tracked.close()
        assert not producer.capture_reconciliation(actor,uuid4(),uuid4(),'US',uuid4())
    asyncio.run(run())
