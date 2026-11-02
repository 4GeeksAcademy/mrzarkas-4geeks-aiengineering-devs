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
from app.inventory.models import InventoryItem
from app.inventory.direct_stock import attempt
from fastapi.exceptions import RequestValidationError
from app.reference_data.models import Clinic, Jurisdiction
from app.telemetry import incident_producer, inventory_direct_stock_producer as producer
from app.telemetry.schemas import TelemetryReceipt
from app.telemetry.server import ServerQueue
from test_telemetry_incident_producer import settings
from test_telemetry_shared import shared
from test_telemetry_context import telemetry


@pytest.mark.parametrize('region', ['US', 'UK'])
@pytest.mark.parametrize('kind', ['in', 'out', 'adjust', 'configuration'])
def test_regionally_scoped_minimal_event(monkeypatch, region, kind):
    async def run():
        item_id, clinic_id, country_id, operation_id = uuid4(), uuid4(), uuid4(), uuid4()
        actor = Actor(uuid4(), 'inventoryManager', clinic_ids=(clinic_id,))
        clinic = SimpleNamespace(id=clinic_id, jurisdiction_id=country_id, is_active=True)
        country = SimpleNamespace(id=country_id, key=region, is_active=True)
        class Session:
            async def get(self, model, identity):
                return {InventoryItem: SimpleNamespace(is_active=True), Clinic: clinic, Jurisdiction: country}[model]
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
        assert producer.capture_direct_stock(actor, item_id, clinic_id, kind, operation_id)
        await asyncio.gather(*service.tasks)
        await service.queue.flush()
        event = batches[0]['events'][0]
        assert event['event_type'] == 'stock_direct_update_rejected'
        assert event['sessionId'] is None and event['requestId'] is None
        assert event['properties']['jurisdiction'] == region
        assert event['properties']['channel'] == 'api'
        assert set(event['properties']) == {'jurisdiction', 'environment', 'operationId', 'channel'}
        assert all(str(value) not in json.dumps(event) for value in [actor.id, clinic_id, country_id, operation_id])
        await service.close()
    asyncio.run(run())


@pytest.mark.parametrize('case', ['admin', 'regional', 'auditor', 'scope', 'operator-adjust',
    'item-missing', 'item-inactive', 'clinic-missing', 'clinic-inactive', 'country-missing', 'country-inactive', 'region', 'kind', 'database'])
def test_context_rejects_invalid_attempt(monkeypatch, case):
    clinic_id, country_id = uuid4(), uuid4()
    actor = Actor(uuid4(), {'admin': 'inventoryAdmin', 'regional': 'inventoryRegional',
        'auditor': 'inventoryAuditor', 'operator-adjust': 'inventoryOperator'}.get(case, 'inventoryManager'),
        clinic_ids=() if case == 'scope' else (clinic_id,))
    class Session:
        async def get(self, model, identity):
            if model is InventoryItem:
                return None if case == 'item-missing' else SimpleNamespace(is_active=case != 'item-inactive')
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
        asyncio.run(producer.resolve_attempt(actor, uuid4(), clinic_id, 'correction' if case == 'kind' else 'adjust'))



@pytest.mark.parametrize('case', ['positive', 'null', 'nested', 'missing', 'bad-kind', 'bad-id', 'global', 'wrong-error', 'wrong-method'])
def test_explicit_detector(case):
    body = dict(item_id=str(uuid4()), clinic_id=str(uuid4()), kind='in', stock=None if case == 'null' else 7)
    if case == 'missing': body.pop('stock')
    if case == 'nested': body = dict(item_id=body['item_id'], clinic_id=body['clinic_id'], kind='in', nested={'stock': 7})
    if case == 'bad-kind': body['kind'] = 'correction'
    if case == 'bad-id': body['clinic_id'] = 'bad'
    error = RequestValidationError([dict(type='value_error' if case == 'wrong-error' else 'extra_forbidden', loc=('body','stock'))], body=body)
    request = SimpleNamespace(method='PATCH' if case == 'wrong-method' else 'POST', path_params={})
    result = attempt(request, error, '/inventory/items' if case == 'global' else '/inventory/movements')
    assert (result is not None) == (case in {'positive', 'null'})

@pytest.mark.integration
def test_postgres_direct_stock_preserves_contract_and_state(monkeypatch):
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
        from app.inventory.models import InventoryAudit, InventoryAccessDenial
        async with factory() as observer:
            audit_before = await observer.scalar(select(func.count()).select_from(InventoryAudit).where(InventoryAudit.item_id == configured.id))
            denials_before = await observer.scalar(select(func.count()).select_from(InventoryAccessDenial).where(InventoryAccessDenial.item_id == configured.id))
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
                    config_route = f'/inventory/items/{configured.id}/clinics/{clinic.id}/configuration'
                    for route, payload in [('/inventory/movements', dict(base, stock=999)),
                                           (config_route, dict(reorder_point=2, stock=None))]:
                        service.closed = True
                        baseline = await client.post(route, json=payload, headers={'Authorization': 'Bearer ' + token})
                        service.closed = False
                        response = await client.post(route, json=payload, headers={'Authorization': 'Bearer ' + token})
                        assert response.status_code == baseline.status_code == 422
                        assert response.json() == baseline.json()
                        await asyncio.gather(*service.tasks)
                    for payload in [dict(base, other=999), dict(base, nested={'stock': 2})]:
                        response = await client.post('/inventory/movements', json=payload, headers={'Authorization': 'Bearer ' + token})
                        assert response.status_code == 422
                        await asyncio.gather(*service.tasks)
                response = await client.post('/inventory/movements', json=dict(base, quantity=0),
                    headers={'Authorization': 'Bearer ' + token})
                assert response.status_code == 422
                from app.inventory import access_audit
                original_hook = access_audit.capture_direct_stock
                def failing_hook(*args):
                    raise RuntimeError('synthetic capture failure')
                monkeypatch.setattr(access_audit, 'capture_direct_stock', failing_hook)
                response = await client.post(config_route, json=dict(reorder_point=2, stock=None), headers={'Authorization': 'Bearer ' + token})
                assert response.status_code == 422 and response.json() == baseline.json()
                monkeypatch.setattr(access_audit, 'capture_direct_stock', original_hook)
            while service.queue.pending:
                await service.queue.flush()
            validations = [e for e in events if e['event_type'] == 'stock_direct_update_rejected']
            assert len(validations) == 4
            assert not any(e['event_type'] == 'inventory_validation_failed' for e in events)
            assert {e['properties']['jurisdiction'] for e in validations} == {'US','UK'}
            async with factory() as observer:
                assert await observer.scalar(select(func.count()).select_from(InventoryAudit).where(InventoryAudit.item_id == configured.id)) == audit_before
                assert await observer.scalar(select(func.count()).select_from(InventoryAccessDenial).where(InventoryAccessDenial.item_id == configured.id)) == denials_before
                assert await observer.scalar(select(func.count()).select_from(InventoryMovement).where(
                    InventoryMovement.item_id.in_([configured.id, unconfigured.id]))) == 0
                from app.inventory.models import InventoryClinicItem
                assert (await observer.get(InventoryClinicItem, (configured.id, c1.id))).reorder_point == 2
                assert (await observer.get(InventoryClinicItem, (configured.id, c2.id))).reorder_point == 2
        finally:
            if old is None:
                app.dependency_overrides.pop(get_session, None)
            else:
                app.dependency_overrides[get_session] = old
            await service.close()
            await engine.dispose()
    asyncio.run(run())

@pytest.mark.parametrize('failure', ['lookup', 'timeout', 'cancel'])
def test_failed_preparation_is_discarded(monkeypatch, failure):
    async def run():
        async def resolve(*args):
            if failure == 'timeout': await asyncio.sleep(1)
            if failure == 'cancel': raise asyncio.CancelledError()
            raise ValueError('synthetic')
        monkeypatch.setattr(producer, 'resolve_attempt', resolve)
        service = incident_producer.IncidentProducer(shared(settings()))
        monkeypatch.setattr(incident_producer, '_producer', service)
        assert producer.capture_direct_stock(Actor(uuid4(),'inventoryManager'), uuid4(), uuid4(), 'in', uuid4())
        await asyncio.gather(*service.tasks, return_exceptions=True)
        assert service.discarded == 1 and not service.queue.pending
        await service.close()
    asyncio.run(run())


def test_disabled_closed_invalid_and_quota(monkeypatch):
    monkeypatch.setattr(incident_producer, '_producer', None)
    assert not producer.capture_direct_stock(None,None,None,None,None)
    async def run():
        service = incident_producer.IncidentProducer(shared(settings()))
        monkeypatch.setattr(incident_producer, '_producer', service)
        actor=Actor(uuid4(),'inventoryManager')
        assert not producer.capture_direct_stock(actor,uuid4(),uuid4(),'invalid',uuid4())
        service.tasks=set(range(16))
        assert not producer.capture_direct_stock(actor,uuid4(),uuid4(),'in',uuid4())
        service.tasks.clear()
        await service.close()
        assert not producer.capture_direct_stock(actor,uuid4(),uuid4(),'in',uuid4())
    asyncio.run(run())


def test_browser_cannot_assert_direct_stock(telemetry):
    from datetime import UTC, datetime
    _, request = telemetry
    context = request('/telemetry/context', {'clinicId': None}).json()
    event = dict(eventId=str(uuid4()), timestamp=datetime.now(UTC).isoformat(), schemaVersion='1.3.0',
        sessionId=context['sessionId'], userId=context['userId'], requestId=None,
        event_type='stock_direct_update_rejected', properties=dict(jurisdiction='US', environment='test',
            operationId='ps_'+'a'*64, channel='api'))
    response = request('/telemetry/events', {'events':[event]}, headers={'X-Telemetry-Context':context['contextToken']})
    assert response.status_code == 403
