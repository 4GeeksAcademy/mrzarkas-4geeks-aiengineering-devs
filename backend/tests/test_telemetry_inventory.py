"""Synthetic confirmed-movement capture and negative authorization boundaries."""
import asyncio
import json
from contextlib import asynccontextmanager
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.auth.dependencies import Actor
from app.inventory.models import InventoryMovement
from app.reference_data.models import Clinic, Jurisdiction
from app.telemetry import inventory_producer as producer, incident_producer
from app.telemetry.identity import region_settings
from app.telemetry.server import ServerQueue
from app.telemetry.schemas import TelemetryReceipt
from test_telemetry_incident_producer import settings
from test_telemetry_shared import shared
from test_telemetry_context import telemetry


@pytest.mark.parametrize('region', ['US', 'UK'])
@pytest.mark.parametrize('kind', ['in', 'out', 'adjust'])
def test_scoped_source_and_opaque_events(monkeypatch, region, kind):
    async def run():
        movement_id, item_id, clinic_id, country_id = [uuid4() for _ in range(4)]
        actor = Actor(uuid4(), 'inventoryManager', clinic_ids=(clinic_id,))
        movement = SimpleNamespace(id=movement_id, item_id=item_id, clinic_id=clinic_id,
            actor_id=actor.id, result='accepted', kind=kind,
            jurisdiction_id=country_id, jurisdiction_key=region)
        clinic = SimpleNamespace(id=clinic_id, jurisdiction_id=country_id, is_active=True)
        country = SimpleNamespace(id=country_id, key=region, is_active=True)
        class Session:
            async def get(self, model, identity):
                return {InventoryMovement: movement, Clinic: clinic, Jurisdiction: country}[model]
        @asynccontextmanager
        async def factory():
            yield Session()
        monkeypatch.setattr(producer.database, 'SessionLocal', factory)
        config = shared(settings())
        batches = []
        async def sink(body):
            batches.append(json.loads(body))
            return TelemetryReceipt(received=len(batches[-1]['events']))
        service = incident_producer.IncidentProducer(config, queue=ServerQueue(sink=sink))
        monkeypatch.setattr(incident_producer, '_producer', service)
        assert producer.capture_inventory(actor, movement_id)
        await asyncio.gather(*service.tasks)
        await service.queue.flush()
        event = batches[0]['events'][0]
        assert event['event_type'] == producer.EVENTS[kind]
        assert event['sessionId'] is None and event['requestId'] is None
        assert event['properties']['jurisdiction'] == region
        expected = {'jurisdiction', 'environment', 'operationId', 'movementId'}
        assert set(event['properties']) == (expected if kind == 'adjust' else expected | {'itemId'})
        assert event['properties']['operationId'] != event['properties']['movementId']
        assert all(str(value) not in json.dumps(event) for value in [actor.id, movement_id, item_id, clinic_id, country_id])
        await service.close()
    asyncio.run(run())


@pytest.mark.parametrize('case', ['missing', 'actor', 'correction', 'result', 'scope',
    'admin', 'regional', 'auditor', 'operator-adjust', 'clinic-missing', 'inactive',
    'country-missing', 'country-inactive', 'country-id', 'country-key', 'unsupported'])
def test_source_rejects_invalid_or_unauthorized_facts(monkeypatch, case):
    clinic_id, country_id = uuid4(), uuid4()
    role = {'admin': 'inventoryAdmin', 'regional': 'inventoryRegional',
            'auditor': 'inventoryAuditor', 'operator-adjust': 'inventoryOperator'}.get(case, 'inventoryManager')
    actor = Actor(uuid4(), role, clinic_ids=() if case == 'scope' else (clinic_id,))
    movement = SimpleNamespace(id=uuid4(), item_id=uuid4(), clinic_id=clinic_id,
        actor_id=uuid4() if case == 'actor' else actor.id, result='denied' if case == 'result' else 'accepted',
        kind='correction' if case == 'correction' else 'adjust',
        jurisdiction_id=uuid4() if case == 'country-id' else country_id,
        jurisdiction_key='UK' if case == 'country-key' else 'US')
    clinic = SimpleNamespace(id=clinic_id, jurisdiction_id=country_id, is_active=case != 'inactive')
    country = SimpleNamespace(id=country_id, key='ZZ' if case == 'unsupported' else 'US', is_active=case != 'country-inactive')
    class Session:
        async def get(self, model, identity):
            return {InventoryMovement: None if case == 'missing' else movement,
                    Clinic: None if case == 'clinic-missing' else clinic,
                    Jurisdiction: None if case == 'country-missing' else country}[model]
    @asynccontextmanager
    async def factory():
        yield Session()
    monkeypatch.setattr(producer.database, 'SessionLocal', factory)
    with pytest.raises((ValueError, HTTPException)):
        asyncio.run(producer.resolve_movement(actor, movement.id))


@pytest.mark.parametrize('failure', ['timeout', 'lookup', 'cancel'])
def test_preparation_failure_has_no_general_fallback(monkeypatch, failure):
    async def run():
        async def resolve(*args):
            if failure == 'lookup':
                raise ValueError('Synthetic sensitive detail')
            await asyncio.sleep(10)
        monkeypatch.setattr(producer, 'resolve_movement', resolve)
        service = incident_producer.IncidentProducer(settings())
        monkeypatch.setattr(incident_producer, '_producer', service)
        assert producer.capture_inventory(Actor(uuid4(), 'inventoryManager'), uuid4())
        if failure == 'cancel':
            await asyncio.sleep(0)
            await service.close()
        else:
            await asyncio.gather(*service.tasks)
            assert service.discarded == 1 and not service.queue.pending
            await service.close()
    asyncio.run(run())


def test_hmac_version_region_purpose_and_configuration_separation():
    config, identity = shared(settings()), uuid4()
    us, uk = region_settings(config, 'US'), region_settings(config, 'UK')
    first = producer.resource_id(us, 'inventory_movement', identity)
    assert first == producer.resource_id(us, 'inventory_movement', identity)
    assert first != producer.resource_id(uk, 'inventory_movement', identity)
    assert first != producer.resource_id(us, 'inventory_operation', identity)
    assert first != producer.resource_id(us, 'inventory_item', identity)
    assert first != incident_producer.resource_id(us, 'audit', identity)
    us.telemetry_key_version = 'v2'
    assert first != producer.resource_id(us, 'inventory_movement', identity)
    us.telemetry_enabled = False
    with pytest.raises(ValueError):
        producer.resource_id(us, 'inventory_movement', identity)


@pytest.mark.parametrize('failure', [None, 'business', 'commit', 'capture'])
def test_hook_only_after_successful_commit(monkeypatch, failure):
    from app.inventory import router
    calls = []
    actor = Actor(uuid4(), 'inventoryManager')
    created = SimpleNamespace(id=uuid4())
    class Session:
        committed = False
        @asynccontextmanager
        async def begin(self):
            yield
            if failure == 'commit':
                raise RuntimeError('Synthetic commit failure')
            self.committed = True
    session = Session()
    async def movement(*args):
        if failure == 'business':
            raise RuntimeError('Synthetic validation failure')
        return created
    def capture(observed, identity):
        assert session.committed and observed == actor and identity == created.id
        calls.append(identity)
        if failure == 'capture':
            raise RuntimeError('Synthetic telemetry failure')
    monkeypatch.setattr(router.svc, 'movement', movement)
    monkeypatch.setattr(router, 'capture_inventory', capture)
    if failure in {'business', 'commit'}:
        with pytest.raises(RuntimeError):
            asyncio.run(router.movement(None, actor, session))
        assert not calls
    else:
        assert asyncio.run(router.movement(None, actor, session)) is created
        assert calls == [created.id]


def test_disabled_closed_invalid_and_saturated_capture(monkeypatch):
    monkeypatch.setattr(incident_producer, '_producer', None)
    assert not producer.capture_inventory(None, None)
    async def run():
        service = incident_producer.IncidentProducer(settings())
        monkeypatch.setattr(incident_producer, '_producer', service)
        assert not producer.capture_inventory(Actor(uuid4(), 'inventoryManager'), 'invalid')
        service.tasks = set(range(16))
        assert not producer.capture_inventory(Actor(uuid4(), 'inventoryManager'), uuid4())
        service.tasks.clear()
        await service.close()
        assert not producer.capture_inventory(Actor(uuid4(), 'inventoryManager'), uuid4())
    asyncio.run(run())


@pytest.mark.integration
def test_postgres_committed_movements_both_regions(monkeypatch):
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy import select
    from app.inventory import router, service as inventory
    from app.inventory.schemas import ItemCreate, ClinicConfig, MovementCreate
    from app.reference_data import seed
    from test_inventory import isolated_url, setup_fixture

    async def run():
        engine = create_async_engine(isolated_url())
        factory = async_sessionmaker(engine, expire_on_commit=False)
        monkeypatch.setattr(producer.database, 'SessionLocal', factory)
        monkeypatch.setattr(seed, 'SessionLocal', factory)
        await seed.seed_reference_data()
        batches = []
        async def sink(body):
            batch = json.loads(body)
            batches.extend(batch['events'])
            return TelemetryReceipt(received=len(batch['events']))
        service = incident_producer.IncidentProducer(shared(settings()), queue=ServerQueue(sink=sink))
        monkeypatch.setattr(incident_producer, '_producer', service)
        try:
            async with factory() as session:
                async with session.begin():
                    c1, c2, admin, _, _ = await setup_fixture(session)
                    for clinic, region in [(c1, 'US'), (c2, 'UK')]:
                        country = await session.scalar(select(Jurisdiction).where(Jurisdiction.key == region))
                        clinic.jurisdiction_id = country.id
                    item = await inventory.create_item(session, admin, ItemCreate(
                        title='Synthetic telemetry gauze', product_code='SYN-TEL-' + str(uuid4()), unit='piece'))
                    manager = Actor(uuid4(), 'inventoryManager', clinic_ids=(c1.id, c2.id))
                    for clinic in (c1, c2):
                        await inventory.configure(session, manager, item.id, clinic.id, ClinicConfig(reorder_point=2))
                for clinic in (c1, c2):
                    for kind in ('in', 'out', 'adjust'):
                        payload = dict(item_id=item.id, clinic_id=clinic.id, kind=kind)
                        payload.update(counted_quantity=4, reason='Synthetic count') if kind == 'adjust' else payload.update(quantity=5 if kind == 'in' else 1)
                        created = await router.movement(MovementCreate(**payload), manager, session)
                        await asyncio.gather(*service.tasks)
                        async with factory() as observer:
                            assert await observer.get(InventoryMovement, created.id) is not None
                before = len(service.queue.pending)
                with pytest.raises(HTTPException):
                    await router.movement(MovementCreate(item_id=item.id, clinic_id=c1.id, kind='out', quantity=1000), manager, session)
                assert len(service.queue.pending) == before
            while service.queue.pending:
                await service.queue.flush()
            assert len(batches) == 6
            assert {(e['event_type'], e['properties']['jurisdiction']) for e in batches} == {
                (event, region) for event in producer.EVENTS.values() for region in ('US', 'UK')}
            assert 'Synthetic count' not in json.dumps(batches)
        finally:
            await service.close()
            await engine.dispose()
    asyncio.run(run())


def test_browser_rejects_inventory_facts(telemetry):
    from datetime import UTC, datetime
    config, request = telemetry
    context = request('/telemetry/context', {'clinicId': None}).json()
    for kind, event_type in producer.EVENTS.items():
        properties = dict(jurisdiction='US', environment='test', operationId='ps_' + 'a'*64,
                          movementId='ps_' + 'b'*64)
        if kind != 'adjust':
            properties['itemId'] = 'ps_' + 'c'*64
        event = dict(eventId=str(uuid4()), timestamp=datetime.now(UTC).isoformat(),
                     schemaVersion='1.3.0', event_type=event_type, requestId=None,
                     sessionId=context['sessionId'], userId=context['userId'], properties=properties)
        response = request('/telemetry/events', {'events': [event]},
                           headers={'X-Telemetry-Context': context['contextToken']})
        assert response.status_code == 403
        assert response.json()['detail'] == 'Event producer unavailable'
