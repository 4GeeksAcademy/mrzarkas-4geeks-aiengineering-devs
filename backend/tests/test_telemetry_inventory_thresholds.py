"""Synthetic comparable crossings, savepoint isolation and durable episode identity."""
import asyncio
import json
from contextlib import asynccontextmanager
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.auth.dependencies import Actor
from app.inventory import thresholds, router, service as inventory
from app.inventory.threshold_models import InventoryThresholdState, InventoryThresholdTransition
from app.telemetry import inventory_threshold_producer as producer, incident_producer
from app.telemetry.schemas import TelemetryReceipt
from app.telemetry.server import ServerQueue
from test_telemetry_incident_producer import settings
from test_telemetry_shared import shared
from test_telemetry_context import telemetry
from fastapi import HTTPException


@pytest.mark.parametrize('before,after', [(5, 4), (6, 0)])
def test_activation_crossing(before, after):
    kind, episode, active = thresholds.crossing(before, after, 5, None, None)
    assert kind == 'activated' and episode == active


@pytest.mark.parametrize('before,after', [(4, 5), (0, 8)])
def test_clear_reuses_episode(before, after):
    episode = uuid4()
    assert thresholds.crossing(before, after, 5, 5, episode) == ('cleared', episode, None)


@pytest.mark.parametrize('before,after', [(5, 5), (9, 5), (4, 4), (3, 2), (1, 5)])
def test_no_cross_or_unknown_legacy_episode(before, after):
    assert thresholds.crossing(before, after, 5, None, None) == (None, None, None)


def test_changed_threshold_and_missed_recovery_invalidate_state():
    old = uuid4()
    assert thresholds.crossing(4, 6, 5, 10, old) == (None, None, None)
    kind, episode, active = thresholds.crossing(5, 4, 5, 5, old)
    assert kind == 'activated' and episode == active and episode != old
    assert thresholds.crossing(3, 3, 5, 5, old) == (None, None, old)


@pytest.mark.parametrize('operation', ['movement', 'correction'])
@pytest.mark.parametrize('failure', [None, 'commit', 'capture'])
def test_threshold_hook_only_after_commit(monkeypatch, operation, failure):
    actor, transition = Actor(uuid4(), 'inventoryManager'), uuid4()
    created = SimpleNamespace(id=uuid4())
    calls = []
    class Session:
        committed = False
        @asynccontextmanager
        async def begin(self):
            yield
            if failure == 'commit':
                raise RuntimeError('Synthetic commit failure')
            self.committed = True
    session = Session()
    async def create(*args): return created
    async def observe(*args): return transition
    def capture(observed, identity):
        assert session.committed and observed == actor and identity == transition
        calls.append(identity)
        if failure == 'capture': raise RuntimeError('Synthetic telemetry failure')
    monkeypatch.setattr(router.svc, 'movement' if operation == 'movement' else 'correct', create)
    monkeypatch.setattr(router, 'observe_threshold', observe)
    monkeypatch.setattr(router, 'capture_threshold', capture)
    monkeypatch.setattr(router, 'capture_inventory', lambda *args: None)
    async def run():
        if operation == 'movement': return await router.movement(None, actor, session)
        return await router.correction(uuid4(), SimpleNamespace(reason='Synthetic'), actor, session)
    if failure == 'commit':
        with pytest.raises(RuntimeError): asyncio.run(run())
        assert not calls
    else:
        assert asyncio.run(run()) is created and calls == [transition]


@pytest.mark.parametrize('region', ['US', 'UK'])
def test_producer_minimal_paired_identifiers(monkeypatch, region):
    async def run():
        actor, episode, item, clinic = Actor(uuid4(), 'inventoryManager'), uuid4(), uuid4(), uuid4()
        events = []
        async def sink(body):
            batch = json.loads(body); events.extend(batch['events'])
            return TelemetryReceipt(received=len(batch['events']))
        service = incident_producer.IncidentProducer(shared(settings()), queue=ServerQueue(sink=sink))
        monkeypatch.setattr(incident_producer, '_producer', service)
        for kind in ('activated', 'cleared'):
            async def resolve(*args): return kind, episode, item, clinic, region
            monkeypatch.setattr(producer, 'resolve_transition', resolve)
            assert producer.capture_threshold(actor, uuid4())
            await asyncio.gather(*service.tasks)
        await service.queue.flush()
        assert len(events) == 2
        assert events[0]['properties'] == events[1]['properties']
        assert set(events[0]['properties']) == {'jurisdiction', 'environment', 'itemId', 'scopeId', 'episodeId'}
        assert all(str(value) not in json.dumps(events) for value in [actor.id, episode, item, clinic])
        await service.close()
    asyncio.run(run())


@pytest.mark.parametrize('case', ['missing', 'kind', 'movement', 'actor', 'result', 'role', 'scope',
    'clinic', 'inactive', 'country', 'country-inactive', 'historical', 'movement-country'])
def test_invalid_transition_is_not_exportable(monkeypatch, case):
    from app.inventory.models import InventoryMovement
    from app.reference_data.models import Clinic, Jurisdiction
    clinic, country = uuid4(), uuid4()
    actor = Actor(uuid4(), 'inventoryAdmin' if case == 'role' else 'inventoryManager', clinic_ids=() if case == 'scope' else (clinic,))
    transition = SimpleNamespace(kind='unknown' if case == 'kind' else 'activated', movement_id=uuid4(),
        jurisdiction_id=uuid4() if case == 'historical' else country, jurisdiction_key='US')
    movement = SimpleNamespace(actor_id=uuid4() if case == 'actor' else actor.id,
        result='denied' if case == 'result' else 'accepted', kind='out', clinic_id=clinic,
        jurisdiction_id=country, jurisdiction_key='UK' if case == 'movement-country' else 'US')
    class Session:
        async def get(self, model, identity):
            return {InventoryThresholdTransition: None if case == 'missing' else transition,
                InventoryMovement: None if case == 'movement' else movement,
                Clinic: None if case == 'clinic' else SimpleNamespace(id=clinic, jurisdiction_id=country, is_active=case != 'inactive'),
                Jurisdiction: None if case == 'country' else SimpleNamespace(id=country, key='US', is_active=case != 'country-inactive')}[model]
    @asynccontextmanager
    async def factory(): yield Session()
    monkeypatch.setattr(producer.database, 'SessionLocal', factory)
    with pytest.raises((ValueError, HTTPException)):
        asyncio.run(producer.resolve_transition(actor, uuid4()))


@pytest.mark.parametrize('failure', ['lookup', 'timeout', 'cancel'])
def test_prepare_failure_never_uses_general_fallback(monkeypatch, failure):
    async def run():
        async def resolve(*args):
            if failure == 'lookup': raise ValueError('Synthetic unavailable')
            await asyncio.sleep(10)
        monkeypatch.setattr(producer, 'resolve_transition', resolve)
        service = incident_producer.IncidentProducer(settings())
        monkeypatch.setattr(incident_producer, '_producer', service)
        assert producer.capture_threshold(Actor(uuid4(), 'inventoryManager'), uuid4())
        if failure == 'cancel':
            await asyncio.sleep(0); await service.close()
        else:
            await asyncio.gather(*service.tasks)
            assert service.discarded == 1 and not service.queue.pending
            await service.close()
    asyncio.run(run())


def test_optional_limits_and_lifecycle(monkeypatch):
    monkeypatch.setattr(incident_producer, '_producer', None)
    assert not producer.capture_threshold(None, None)
    async def run():
        service = incident_producer.IncidentProducer(settings())
        monkeypatch.setattr(incident_producer, '_producer', service)
        actor = Actor(uuid4(), 'inventoryManager')
        assert not producer.capture_threshold(actor, None)
        assert not producer.capture_threshold(actor, 'invalid')
        service.tasks = set(range(16))
        assert not producer.capture_threshold(actor, uuid4())
        service.tasks.clear(); await service.close()
        assert not producer.capture_threshold(actor, uuid4())
    asyncio.run(run())


def test_browser_rejects_threshold_facts(telemetry):
    from datetime import UTC, datetime
    _, request = telemetry
    context = request('/telemetry/context', {'clinicId': None}).json()
    for kind in ('activated', 'cleared'):
        event = dict(eventId=str(uuid4()), timestamp=datetime.now(UTC).isoformat(), schemaVersion='1.3.0',
            sessionId=context['sessionId'], userId=context['userId'], requestId=None,
            event_type='inventory_threshold_' + kind, properties=dict(jurisdiction='US', environment='test',
                itemId='ps_' + 'a'*64, scopeId='ps_' + 'b'*64, episodeId='ps_' + 'c'*64))
        response = request('/telemetry/events', {'events': [event]}, headers={'X-Telemetry-Context': context['contextToken']})
        assert response.status_code == 403 and response.json()['detail'] == 'Event producer unavailable'


@pytest.mark.integration
@pytest.mark.parametrize('region', ['US', 'UK'])
def test_postgres_lot_aggregation_pairing_config_and_savepoint(monkeypatch, region):
    from sqlalchemy import select, func, text
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.reference_data import seed
    from app.reference_data.models import Jurisdiction
    from app.inventory.schemas import ItemCreate, ClinicConfig, LotCreate, MovementCreate, ReasonRequest
    from app.inventory.models import InventoryMovement
    from test_inventory import isolated_url, setup_fixture

    async def run():
        engine = create_async_engine(isolated_url())
        factory = async_sessionmaker(engine, expire_on_commit=False)
        monkeypatch.setattr(seed, 'SessionLocal', factory)
        monkeypatch.setattr(producer.database, 'SessionLocal', factory)
        await seed.seed_reference_data()
        async with factory() as session, session.begin():
            c1, _, admin, _, _ = await setup_fixture(session)
            c1.jurisdiction_id = (await session.scalar(select(Jurisdiction).where(Jurisdiction.key == region))).id
            actor = Actor(uuid4(), 'inventoryManager', clinic_ids=(c1.id,))
            item = await inventory.create_item(session, admin, ItemCreate(title='Synthetic thresholds', product_code='SYN-EP-' + str(uuid4()), unit='piece', uses_lots=True))
            await inventory.configure(session, actor, item.id, c1.id, ClinicConfig(reorder_point=5))
            lots = [await inventory.create_lot(session, admin, item.id, LotCreate(code='SYN-' + str(uuid4()))) for _ in range(2)]
            for lot in lots:
                await inventory.movement(session, actor, MovementCreate(item_id=item.id, clinic_id=c1.id, lot_id=lot.id, kind='in', quantity=5))
        events = []
        async def sink(body):
            batch = json.loads(body); events.extend(batch['events'])
            return TelemetryReceipt(received=len(batch['events']))
        service = incident_producer.IncidentProducer(shared(settings()), queue=ServerQueue(sink=sink))
        monkeypatch.setattr(incident_producer, '_producer', service)
        try:
            async def move(lot, kind='out', amount=1):
                async with factory() as session:
                    created = await router.movement(MovementCreate(item_id=item.id, clinic_id=c1.id, lot_id=lot.id, kind=kind, quantity=amount), actor, session)
                await asyncio.gather(*service.tasks)
                return created
            await move(lots[0])  # 10→9 no crossing
            await move(lots[0], amount=4)  # 9→5 equality, no episode
            activation = await move(lots[1])  # 5→4 activate
            under = await move(lots[1])  # 4→3 no duplicate
            async with factory() as session:
                await router.correction(under.id, ReasonRequest(reason='Synthetic compensation'), actor, session)  #3→4
            await asyncio.gather(*service.tasks)
            async with factory() as session:
                await router.correction(activation.id, ReasonRequest(reason='Synthetic compensation'), actor, session)  #4→5 clear
            await asyncio.gather(*service.tasks)
            await move(lots[1])  #5→4 new episode
            async with factory() as session, session.begin():
                await inventory.configure(session, actor, item.id, c1.id, ClinicConfig(reorder_point=10))
            await move(lots[1], 'in', 2)  #4→6 changed threshold invalidates old episode, no clear
            await move(lots[1], 'in', 4)  #6→10 unknown low baseline, no fictitious clear
            await move(lots[1])  #10→9 genuine activation under new threshold
            async with factory() as observer:
                transitions = (await observer.scalars(select(InventoryThresholdTransition).join(InventoryMovement,
                    InventoryMovement.id == InventoryThresholdTransition.movement_id).where(InventoryMovement.item_id == item.id)
                    .order_by(InventoryThresholdTransition.occurred_at))).all()
                assert [value.kind for value in transitions] == ['activated', 'cleared', 'activated', 'activated']
                assert transitions[0].episode_id == transitions[1].episode_id
                assert len({value.episode_id for value in transitions}) == 3
                with pytest.raises(Exception, match='append-only'):
                    async with observer.begin_nested():
                        await observer.execute(text('UPDATE inventory_threshold_transition SET threshold=20 WHERE id=:id'), {'id': transitions[0].id})
                state = await observer.get(InventoryThresholdState, (item.id, c1.id))
                assert state.episode_id == transitions[-1].episode_id and state.threshold == 10
            # SQL failure in the observer savepoint must not abort the real movement.
            async def fail_quantity(session, *args): await session.execute(text('SELECT 1/0'))
            monkeypatch.setattr(thresholds, 'quantity', fail_quantity)
            created = await move(lots[1])  #9→8 still persists
            async with factory() as observer:
                assert await observer.get(InventoryMovement, created.id) is not None
                assert await inventory.quantity(observer, item.id, c1.id) == 8
            while service.queue.pending: await service.queue.flush()
            captured = [event for event in events if event['event_type'].startswith('inventory_threshold_')]
            assert len(captured) == 4
            assert captured[0]['properties']['episodeId'] == captured[1]['properties']['episodeId']
        finally:
            await service.close(); await engine.dispose()
    asyncio.run(run())


@pytest.mark.integration
def test_postgres_concurrent_crossing_and_outer_rollback(monkeypatch):
    from sqlalchemy import select, func
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.reference_data import seed
    from app.reference_data.models import Jurisdiction
    from app.inventory.schemas import ItemCreate, ClinicConfig, MovementCreate
    from app.inventory.models import InventoryMovement
    from test_inventory import isolated_url, setup_fixture

    async def run():
        engine = create_async_engine(isolated_url()); factory = async_sessionmaker(engine, expire_on_commit=False)
        monkeypatch.setattr(seed, 'SessionLocal', factory); await seed.seed_reference_data()
        async with factory() as session, session.begin():
            clinic, _, admin, _, _ = await setup_fixture(session)
            clinic.jurisdiction_id = (await session.scalar(select(Jurisdiction).where(Jurisdiction.key == 'US'))).id
            actor = Actor(uuid4(), 'inventoryManager', clinic_ids=(clinic.id,))
            item = await inventory.create_item(session, admin, ItemCreate(title='Synthetic concurrent threshold', product_code='SYN-CON-' + str(uuid4()), unit='piece'))
            await inventory.configure(session, actor, item.id, clinic.id, ClinicConfig(reorder_point=5))
            await inventory.movement(session, actor, MovementCreate(item_id=item.id, clinic_id=clinic.id, kind='in', quantity=6))
        async def out():
            async with factory() as session:
                await router.movement(MovementCreate(item_id=item.id, clinic_id=clinic.id, kind='out', quantity=1), actor, session)
        await asyncio.gather(out(), out())  #6→5→4: exactly one transition
        async with factory() as session:
            await router.movement(MovementCreate(item_id=item.id, clinic_id=clinic.id, kind='adjust', counted_quantity=4, reason='Synthetic equal count'), actor, session)
        async with factory() as observer:
            rows = (await observer.scalars(select(InventoryThresholdTransition).join(InventoryMovement,
                InventoryMovement.id == InventoryThresholdTransition.movement_id).where(InventoryMovement.item_id == item.id))).all()
            assert len(rows) == 1
            episode = rows[0].episode_id
        async with factory() as session:
            with pytest.raises(RuntimeError):
                async with session.begin():
                    movement = await inventory.movement(session, actor, MovementCreate(item_id=item.id, clinic_id=clinic.id, kind='in', quantity=1))
                    assert await thresholds.observe(session, movement) is not None
                    raise RuntimeError('Synthetic outer rollback')
        async with factory() as observer:
            assert await inventory.quantity(observer, item.id, clinic.id) == 4
            state = await observer.get(InventoryThresholdState, (item.id, clinic.id))
            assert state.episode_id == episode
        await engine.dispose()
    asyncio.run(run())
