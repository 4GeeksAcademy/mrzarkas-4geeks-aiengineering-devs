"""Synthetic durable lifecycle, idle boundaries, races and terminal exclusion."""
import asyncio
import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4
import pytest
from fastapi import HTTPException
from app.auth.dependencies import Actor
from app.inventory import flow_lifecycle as lifecycle
from app.inventory.flow_models import InventoryTelemetryFlow as Flow
from app.telemetry import inventory_abandonment_producer as producer, incident_producer
from app.telemetry.identity import region_settings
from app.telemetry.inventory_flow_identity import issue_flow
from app.telemetry.server import ServerQueue
from app.telemetry.schemas import TelemetryReceipt
from test_telemetry_incident_producer import settings
from test_telemetry_shared import shared
from test_telemetry_context import telemetry


@pytest.mark.parametrize('region',['US','UK'])
@pytest.mark.integration
def test_durable_lifecycle_idle_terminal_and_races(monkeypatch,region):
    from sqlalchemy import select, text, update
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.reference_data import seed
    from app.reference_data.models import Jurisdiction
    from app.inventory import service
    from app.inventory.schemas import ItemCreate, ClinicConfig, MovementCreate
    from test_inventory import isolated_url, setup_fixture
    async def run():
        engine=create_async_engine(isolated_url())
        factory=async_sessionmaker(engine,expire_on_commit=False)
        monkeypatch.setattr(lifecycle.database,'SessionLocal',factory)
        monkeypatch.setattr(seed,'SessionLocal',factory)
        await seed.seed_reference_data()
        # Reset only prior synthetic lifecycle fixtures in this disposable DB.
        async with factory() as session, session.begin():
            await session.execute(update(Flow).where(Flow.status == 'open').values(status='uncertain',closed_at=datetime.now(UTC)))
        async with factory() as session,session.begin():
            c1,c2,admin,_,_=await setup_fixture(session)
            clinic=c1 if region=='US' else c2
            country=await session.scalar(select(Jurisdiction).where(Jurisdiction.key==region))
            clinic.jurisdiction_id=country.id
            actor=Actor(uuid4(),'inventoryManager',clinic_ids=(clinic.id,))
            item=await service.create_item(session,admin,ItemCreate(title='Synthetic abandoned',product_code='SYN-AB-'+str(uuid4()),unit='piece'))
            await service.configure(session,actor,item.id,clinic.id,ClinicConfig(reorder_point=2))
        current=[datetime.now(UTC)]
        monkeypatch.setattr(lifecycle,'clock',lambda:current[0])
        monkeypatch.setattr(producer,'clock',lambda:current[0])
        config=shared(settings());scoped=region_settings(config,region)
        events=[]
        async def sink(body):
            batch=json.loads(body);events.extend(batch['events']);return TelemetryReceipt(received=len(batch['events']))
        tracked=incident_producer.IncidentProducer(config,queue=ServerQueue(sink=sink))
        monkeypatch.setattr(incident_producer,'_producer',tracked)
        async def create(direction=None):
            flow,_,_=issue_flow(scoped,actor,clinic.id,item.id,direction,int(datetime.now(UTC).timestamp())+300)
            assert await lifecycle.record(actor,clinic.id,item.id,scoped,flow,'order_started' if direction else 'product_selected',direction)
            return flow
        try:
            flow=await create()
            current[0]+=timedelta(minutes=29,seconds=59)
            assert await producer.sweep(tracked)==0
            current[0]+=timedelta(seconds=1)
            # Two workers cannot both close the same row.
            assert sum(await asyncio.gather(producer.sweep(tracked),producer.sweep(tracked)))==1
            await tracked.queue.flush()
            assert len(events)==1
            assert events[0]['properties']==dict(jurisdiction=region,environment='test',flowId=flow,lastStep='selection',durationMs=1800000)
            assert events[0]['sessionId'] is None and events[0]['requestId'] is None
            assert str(actor.id) not in json.dumps(events)
            assert await producer.sweep(tracked)==0
            async with factory() as observer:
                assert (await observer.get(Flow,flow)).status=='abandoned'
            with pytest.raises(HTTPException):
                await lifecycle.record(actor,clinic.id,item.id,scoped,flow,'order_started','inbound')
            started=await create('inbound')
            current[0]+=timedelta(minutes=20)
            await lifecycle.record(actor,clinic.id,item.id,scoped,started,'confirmation',None)
            current[0]+=timedelta(minutes=20)
            assert await producer.sweep(tracked)==0
            # A real transaction closes the exact flow; a rollback preserves open.
            async with factory() as session:
                with pytest.raises(RuntimeError):
                    async with session.begin():
                        move=await service.movement(session,actor,MovementCreate(item_id=item.id,clinic_id=clinic.id,kind='in',quantity=3))
                        assert await lifecycle.complete(session,move,started)
                        raise RuntimeError('synthetic rollback')
            async with factory() as observer:
                assert (await observer.get(Flow,started)).status=='open'
            async with factory() as session,session.begin():
                move=await service.movement(session,actor,MovementCreate(item_id=item.id,clinic_id=clinic.id,kind='in',quantity=3))
                assert await lifecycle.complete(session,move,started)
            async with factory() as observer:
                assert (await observer.get(Flow,started)).status=='completed'
            unknown=await create('inbound')
            async with factory() as session,session.begin():
                move=await service.movement(session,actor,MovementCreate(item_id=item.id,clinic_id=clinic.id,kind='in',quantity=1))
                assert await lifecycle.complete(session,move,None)
            async with factory() as observer:
                assert (await observer.get(Flow,unknown)).status=='uncertain'
            # Ordinary SQL tracking failure rolls back only its savepoint.
            another=await create('inbound')
            original=lifecycle.clock
            def failure(): raise ValueError('synthetic tracking failure')
            monkeypatch.setattr(lifecycle,'clock',failure)
            async with factory() as session,session.begin():
                move=await service.movement(session,actor,MovementCreate(item_id=item.id,clinic_id=clinic.id,kind='in',quantity=1))
                assert not await lifecycle.complete(session,move,another)
                assert await session.scalar(text('SELECT 1'))==1
            monkeypatch.setattr(lifecycle,'clock',original)
            async with factory() as observer:
                assert (await observer.get(Flow,another)).status=='uncertain'
            # Suppression after tracking failure avoids making a terminal claim.
            tracked.inventory_flow_uncertain=True
            current[0]+=timedelta(minutes=30)
            assert await producer.sweep(tracked)==0
            async with factory() as observer:
                assert (await observer.get(Flow,another)).status=='uncertain'
            with pytest.raises(HTTPException):
                await lifecycle.record(actor,clinic.id,item.id,scoped,'ps_'+'f'*64,'activity',None)
            tracked.inventory_flow_uncertain=False
            active_race=await create('inbound')
            current[0]+=timedelta(minutes=29,seconds=59)
            monkeypatch.setattr(producer,'clock',lambda:current[0]+timedelta(seconds=1))
            async def activity():
                try:
                    return await lifecycle.record(actor,clinic.id,item.id,scoped,active_race,'activity',None)
                except HTTPException as error:
                    assert error.status_code==409
                    return False
            results=await asyncio.gather(activity(),producer.sweep(tracked))
            assert (results[0] is True and results[1]==0) or (results[0] is False and results[1]==1)
            monkeypatch.setattr(producer,'clock',lambda:current[0])
            # A terminal arriving after the idle deadline races under the same lock.
            racing=await create('inbound')
            current[0]+=timedelta(minutes=30)
            async def terminal():
                async with factory() as session,session.begin():
                    move=await service.movement(session,actor,MovementCreate(item_id=item.id,clinic_id=clinic.id,kind='in',quantity=1))
                    assert await lifecycle.complete(session,move,racing)
            await asyncio.gather(terminal(),producer.sweep(tracked))
            async with factory() as observer:
                assert (await observer.get(Flow,racing)).status in {'completed','abandoned'}
            # Batch bound is enforced, and a later sweep drains the remaining row.
            async with factory() as session,session.begin():
                for _ in range(101):
                    session.add(Flow(flow_id='ps_'+uuid4().hex+uuid4().hex,actor_id=actor.id,item_id=item.id,clinic_id=clinic.id,
                        jurisdiction_id=country.id,jurisdiction_key=region,environment='test',key_version=scoped.telemetry_key_version,
                        direction=None,started_at=current[0]-timedelta(minutes=30),last_activity_at=current[0]-timedelta(minutes=30),last_step='selection',status='open'))
            assert await producer.sweep(tracked)==100
            assert await producer.sweep(tracked)==1
            assert await producer.sweep(tracked)==0

        finally:
            await tracked.close();await engine.dispose()
    asyncio.run(run())


def test_browser_cannot_assert_abandonment(telemetry):
    _,request=telemetry
    context=request('/telemetry/context',{'clinicId':None}).json()
    event=dict(eventId=str(uuid4()),timestamp=datetime.now(UTC).isoformat(),schemaVersion='1.3.0',
        sessionId=context['sessionId'],userId=context['userId'],requestId=None,event_type='order_abandoned',
        properties=dict(jurisdiction='US',environment='test',flowId='ps_'+'a'*64,lastStep='selection',durationMs=1800000))
    assert request('/telemetry/events',{'events':[event]},headers={'X-Telemetry-Context':context['contextToken']}).status_code==403


def test_worker_cancel_and_disabled():
    async def run():
        assert await producer.sweep(None)==0
        task=producer.start(SimpleNamespace(closed=False,discarded=0))
        await producer.stop(task)
        assert task.done()
    asyncio.run(run())

@pytest.mark.parametrize('field',['actor_id','item_id','clinic_id','jurisdiction_key','environment','key_version','valid'])
def test_lifecycle_binding(field):
    actor=Actor(uuid4(),'inventoryManager');clinic,item=uuid4(),uuid4()
    config=region_settings(shared(settings()),'US')
    row=SimpleNamespace(actor_id=actor.id,clinic_id=clinic,item_id=item,jurisdiction_key='US',environment='test',key_version=config.telemetry_key_version)
    if field!='valid': setattr(row,field,uuid4() if field.endswith('_id') else 'other')
    assert lifecycle.matches(row,actor,clinic,item,config)==(field=='valid')

@pytest.mark.parametrize('case',['valid','missing-flow','extra','direction','token','new-flow'])
def test_lifecycle_closed_request(case):
    from app.telemetry.inventory_flow_router import FlowRequest
    from pydantic import ValidationError
    payload=dict(action='activity',itemId=uuid4(),clinicId=uuid4(),flowId='ps_'+'a'*64)
    if case=='missing-flow': payload.pop('flowId')
    if case=='extra': payload['quantity']=7
    if case=='direction': payload['direction']='inbound'
    if case=='token': payload['flowToken']='synthetic'
    if case=='new-flow': payload['action']='order_started';payload['direction']='inbound'
    if case=='valid': assert FlowRequest(**payload).action=='activity'
    else:
        with pytest.raises(ValidationError): FlowRequest(**payload)
