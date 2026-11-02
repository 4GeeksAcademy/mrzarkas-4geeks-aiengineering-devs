"""Typed inventory rejections, rollback ordering and privacy boundaries."""
import asyncio
import json
from contextlib import asynccontextmanager
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.auth.dependencies import Actor
from app.inventory import router
from app.inventory.schemas import MovementCreate
from app.inventory.validation import InventoryValidationError, REASONS
from app.reference_data.models import Clinic, Jurisdiction
from app.telemetry import incident_producer, inventory_validation_producer as producer
from app.telemetry.schemas import TelemetryReceipt
from app.telemetry.server import ServerQueue
from test_telemetry_incident_producer import settings
from test_telemetry_shared import shared
from test_telemetry_context import telemetry


@pytest.mark.parametrize('region', ['US', 'UK'])
@pytest.mark.parametrize('reason', sorted(REASONS))
def test_regionally_scoped_minimal_event(monkeypatch, region, reason):
    async def run():
        clinic_id, country_id, operation_id = uuid4(), uuid4(), uuid4()
        actor = Actor(uuid4(), 'inventoryManager', clinic_ids=(clinic_id,))
        clinic = SimpleNamespace(id=clinic_id, jurisdiction_id=country_id, is_active=True)
        country = SimpleNamespace(id=country_id, key=region, is_active=True)
        class Session:
            async def get(self, model, identity):
                return {Clinic: clinic, Jurisdiction: country}[model]
        @asynccontextmanager
        async def factory():
            yield Session()
        monkeypatch.setattr(producer.database, 'SessionLocal', factory)
        batches = []
        async def sink(body):
            batches.append(json.loads(body))
            return TelemetryReceipt(received=len(batches[-1]['events']))
        service = incident_producer.IncidentProducer(shared(settings()), queue=ServerQueue(sink=sink))
        monkeypatch.setattr(incident_producer, '_producer', service)
        assert producer.capture_validation(actor, clinic_id, 'in', operation_id, reason)
        await asyncio.gather(*service.tasks)
        await service.queue.flush()
        event = batches[0]['events'][0]
        assert event['event_type'] == 'inventory_validation_failed'
        assert event['sessionId'] is None and event['requestId'] is None
        assert event['properties']['jurisdiction'] == region
        assert event['properties']['reasonCode'] == reason
        assert set(event['properties']) == {'jurisdiction', 'environment', 'operationId', 'reasonCode'}
        assert all(str(value) not in json.dumps(event) for value in [actor.id, clinic_id, country_id, operation_id])
        await service.close()
    asyncio.run(run())


@pytest.mark.parametrize('case', ['admin', 'regional', 'auditor', 'scope', 'operator-adjust',
    'clinic-missing', 'clinic-inactive', 'country-missing', 'country-inactive', 'region', 'kind', 'database'])
def test_context_rejects_invalid_attempt(monkeypatch, case):
    clinic_id, country_id = uuid4(), uuid4()
    actor = Actor(uuid4(), {'admin': 'inventoryAdmin', 'regional': 'inventoryRegional',
        'auditor': 'inventoryAuditor', 'operator-adjust': 'inventoryOperator'}.get(case, 'inventoryManager'),
        clinic_ids=() if case == 'scope' else (clinic_id,))
    class Session:
        async def get(self, model, identity):
            if model is Clinic:
                return None if case == 'clinic-missing' else SimpleNamespace(id=clinic_id,
                    jurisdiction_id=country_id, is_active=case != 'clinic-inactive')
            return None if case == 'country-missing' else SimpleNamespace(id=country_id,
                is_active=case != 'country-inactive', key='ZZ' if case == 'region' else 'US')
    @asynccontextmanager
    async def factory():
        yield Session()
    monkeypatch.setattr(producer.database, 'SessionLocal', None if case == 'database' else factory)
    with pytest.raises((HTTPException, ValueError)):
        asyncio.run(producer.resolve_attempt(actor, clinic_id, 'correction' if case == 'kind' else 'adjust'))


@pytest.mark.parametrize('case', ['typed', 'hook-failure', 'rollback-failure', 'untyped', 'denial'])
def test_hook_after_rollback_preserves_original_error(monkeypatch, case):
    payload = MovementCreate(item_id=uuid4(), clinic_id=uuid4(), kind='out', quantity=100)
    actor = Actor(uuid4(), 'inventoryManager', clinic_ids=(payload.clinic_id,))
    original = (HTTPException(403, 'Inventory permission denied') if case == 'denial' else
                HTTPException(409, 'Other conflict') if case == 'untyped' else
                InventoryValidationError(409, 'Insufficient stock', 'insufficient_stock'))
    calls = []
    class Session:
        rolled_back = False
        @asynccontextmanager
        async def begin(self):
            try:
                yield
            except Exception:
                if case == 'rollback-failure':
                    raise RuntimeError('Synthetic rollback failure')
                self.rolled_back = True
                raise
    session = Session()
    async def reject(*args):
        raise original
    def capture(observed, clinic_id, kind, operation_id, reason):
        assert session.rolled_back and observed == actor and clinic_id == payload.clinic_id
        assert kind == 'out' and reason == 'insufficient_stock'
        calls.append(operation_id)
        if case == 'hook-failure':
            raise RuntimeError('Synthetic capture failure')
    monkeypatch.setattr(router.svc, 'movement', reject)
    monkeypatch.setattr(router, 'capture_validation', capture)
    with pytest.raises(RuntimeError if case == 'rollback-failure' else HTTPException) as observed:
        asyncio.run(router.movement(payload, actor, session))
    if case != 'rollback-failure':
        assert observed.value is original
    assert len(calls) == (1 if case in {'typed', 'hook-failure'} else 0)


def test_browser_rejects_validation_event(telemetry):
    from datetime import UTC, datetime
    _, request = telemetry
    context = request('/telemetry/context', {'clinicId': None}).json()
    event = dict(eventId=str(uuid4()), timestamp=datetime.now(UTC).isoformat(),
        schemaVersion='1.3.0', sessionId=context['sessionId'], userId=context['userId'], requestId=None,
        event_type='inventory_validation_failed', properties=dict(jurisdiction='US', environment='test',
        operationId='ps_' + 'a'*64, reasonCode='lot'))
    response = request('/telemetry/events', {'events': [event]},
        headers={'X-Telemetry-Context': context['contextToken']})
    assert response.status_code == 403 and response.json()['detail'] == 'Event producer unavailable'


@pytest.mark.parametrize('failure', ['lookup', 'timeout', 'cancel'])
def test_preparation_failures_do_not_emit(monkeypatch, failure):
    async def run():
        async def resolve(*args):
            if failure == 'lookup':
                raise ValueError('Synthetic private error text')
            await asyncio.sleep(10)
        monkeypatch.setattr(producer, 'resolve_attempt', resolve)
        service = incident_producer.IncidentProducer(settings())
        monkeypatch.setattr(incident_producer, '_producer', service)
        assert producer.capture_validation(Actor(uuid4(), 'inventoryManager'), uuid4(), 'in', uuid4(), 'lot')
        if failure == 'cancel':
            await asyncio.sleep(0)
            await service.close()
        else:
            await asyncio.gather(*service.tasks)
            assert service.discarded == 1 and not service.queue.pending
            await service.close()
    asyncio.run(run())


def test_disabled_invalid_closed_and_saturated(monkeypatch):
    monkeypatch.setattr(incident_producer, '_producer', None)
    assert not producer.capture_validation(None, None, None, None, None)
    async def run():
        service = incident_producer.IncidentProducer(settings())
        monkeypatch.setattr(incident_producer, '_producer', service)
        actor = Actor(uuid4(), 'inventoryManager')
        assert not producer.capture_validation(actor, uuid4(), 'in', uuid4(), 'scope')
        assert not producer.capture_validation(actor, uuid4(), 'in', 'invalid', 'lot')
        service.tasks = set(range(16))
        assert not producer.capture_validation(actor, uuid4(), 'in', uuid4(), 'lot')
        service.tasks.clear()
        await service.close()
        assert not producer.capture_validation(actor, uuid4(), 'in', uuid4(), 'lot')
    asyncio.run(run())


@pytest.mark.integration
def test_postgres_rejections_rollback_and_keep_http_contract(monkeypatch):
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy import select, func
    from httpx import ASGITransport, AsyncClient
    from app.db.session import get_session
    from app.auth.security import create_access_token
    from app.inventory.models import InventoryMovement
    from app.inventory import service as inventory
    from app.inventory.schemas import ItemCreate, ClinicConfig
    from app.main import app
    from app.reference_data import seed
    from test_inventory import isolated_url, setup_fixture

    async def run():
        engine = create_async_engine(isolated_url())
        factory = async_sessionmaker(engine, expire_on_commit=False)
        monkeypatch.setattr(seed, 'SessionLocal', factory)
        monkeypatch.setattr(producer.database, 'SessionLocal', factory)
        await seed.seed_reference_data()
        async with factory() as session, session.begin():
            c1, c2, admin, _, _ = await setup_fixture(session)
            for clinic, region in [(c1, 'US'), (c2, 'UK')]:
                clinic.jurisdiction_id = (await session.scalar(select(Jurisdiction).where(Jurisdiction.key == region))).id
            manager = Actor(uuid4(), 'inventoryManager', clinic_ids=(c1.id, c2.id))
            configured = await inventory.create_item(session, admin, ItemCreate(title='Synthetic validation',
                product_code='SYN-VAL-' + str(uuid4()), unit='piece'))
            unconfigured = await inventory.create_item(session, admin, ItemCreate(title='Synthetic unconfigured',
                product_code='SYN-VAL-' + str(uuid4()), unit='piece'))
            for clinic in (c1, c2):
                await inventory.configure(session, manager, configured.id, clinic.id, ClinicConfig(reorder_point=2))
        events = []
        async def sink(body):
            batch = json.loads(body)
            events.extend(batch['events'])
            return TelemetryReceipt(received=len(batch['events']))
        service = incident_producer.IncidentProducer(shared(settings()), queue=ServerQueue(sink=sink))
        monkeypatch.setattr(incident_producer, '_producer', service)
        async def sessions():
            async with factory() as session:
                yield session
        old = app.dependency_overrides.get(get_session)
        app.dependency_overrides[get_session] = sessions
        try:
            token = create_access_token(manager.id, manager.role, clinic_ids=manager.clinic_ids)
            async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
                for clinic in (c1, c2):
                    base = dict(item_id=str(configured.id), clinic_id=str(clinic.id), kind='in', quantity=1)
                    cases = [(dict(base, item_id=str(unconfigured.id)), 409, 'Configure the mandatory clinic reorder point first', 'reference'),
                        (dict(base, lot_id=str(uuid4())), 422, 'Lot requirement does not match the item', 'lot'),
                        (dict(base, unit='pack'), 422, 'Item has no pack presentation', 'unit'),
                        (dict(base, kind='out'), 409, 'Insufficient stock', 'insufficient_stock')]
                    for payload, status, detail, reason in cases:
                        response = await client.post('/inventory/movements', json=payload,
                            headers={'Authorization': 'Bearer ' + token})
                        assert response.status_code == status and response.json() == {'detail': detail}
                        await asyncio.gather(*service.tasks)
                response = await client.post('/inventory/movements', json=dict(base, quantity=0),
                    headers={'Authorization': 'Bearer ' + token})
                assert response.status_code == 422
            while service.queue.pending:
                await service.queue.flush()
            validations = [e for e in events if e['event_type'] == 'inventory_validation_failed']
            assert len(validations) == 8
            assert {(e['properties']['jurisdiction'], e['properties']['reasonCode']) for e in validations} == {
                (region, reason) for region in ('US', 'UK') for reason in REASONS}
            async with factory() as observer:
                assert await observer.scalar(select(func.count()).select_from(InventoryMovement).where(
                    InventoryMovement.item_id.in_([configured.id, unconfigured.id]))) == 0
        finally:
            if old is None:
                app.dependency_overrides.pop(get_session, None)
            else:
                app.dependency_overrides[get_session] = old
            await service.close()
            await engine.dispose()
    asyncio.run(run())
