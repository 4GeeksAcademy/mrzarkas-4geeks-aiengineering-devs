"""Completed clinic-bound views, byte-preserving ASGI observation and scoped capture."""
import asyncio
import json
from contextlib import asynccontextmanager
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.auth.dependencies import Actor
from app.reference_data.models import Clinic, Jurisdiction
from app.telemetry import inventory_view_producer as producer, inventory_view_completion as completion, incident_producer
from app.telemetry.schemas import TelemetryReceipt
from app.telemetry.server import ServerQueue
from test_telemetry_incident_producer import settings
from test_telemetry_shared import shared
from test_telemetry_context import telemetry


@pytest.mark.parametrize('status', [200, 204, 401, 403, 404, 409, 422, 500])
@pytest.mark.parametrize('marked', [True, False])
def test_complete_response_preserved_and_captured_once(monkeypatch, status, marked):
    async def run():
        actor, clinic_id = Actor(uuid4(), 'inventoryOperator'), uuid4()
        calls, sent = [], []
        messages = [{'type': 'http.response.start', 'status': status, 'headers': [(b'x-test', b'synthetic')]},
                    {'type': 'http.response.body', 'body': b'[', 'more_body': True},
                    {'type': 'http.response.body', 'body': b']', 'more_body': False}]
        async def app(scope, receive, send):
            if marked:
                producer.mark_view(SimpleNamespace(scope=scope), actor, clinic_id, 'stock')
            for message in messages:
                await send(message)
        async def send(message):
            sent.append(message.copy())
        def capture(*descriptor):
            assert sent == messages
            calls.append(descriptor)
        monkeypatch.setattr(completion, 'capture_view', capture)
        scope = {'type': 'http', 'state': {producer.STATE_KEY: ('stale',)}}
        await completion.InventoryViewCompletionMiddleware(app)(scope, None, send)
        assert sent == messages
        assert len(calls) == (1 if marked and status < 300 else 0)
        assert producer.STATE_KEY not in scope['state']
    asyncio.run(run())


@pytest.mark.parametrize('failure', ['send', 'cancel', 'app', 'incomplete', 'capture'])
def test_failed_or_incomplete_delivery_never_becomes_success(monkeypatch, failure):
    async def run():
        calls = []
        async def app(scope, receive, send):
            producer.mark_view(SimpleNamespace(scope=scope), Actor(uuid4(), 'inventoryManager'), uuid4(), 'stock')
            await send({'type': 'http.response.start', 'status': 200, 'headers': []})
            if failure == 'app':
                raise RuntimeError('Synthetic serialization failure')
            await send({'type': 'http.response.body', 'body': b'[]', 'more_body': failure == 'incomplete'})
        async def send(message):
            if message['type'] == 'http.response.body':
                if failure == 'send':
                    raise RuntimeError('Synthetic disconnect')
                if failure == 'cancel':
                    raise asyncio.CancelledError()
        def capture(*args):
            calls.append(args)
            raise RuntimeError('Synthetic capture failure')
        monkeypatch.setattr(completion, 'capture_view', capture)
        scope = {'type': 'http', 'state': {}}
        observed = completion.InventoryViewCompletionMiddleware(app)
        if failure in {'send', 'app', 'cancel'}:
            with pytest.raises(asyncio.CancelledError if failure == 'cancel' else RuntimeError):
                await observed(scope, None, send)
        else:
            await observed(scope, None, send)
        assert len(calls) == (1 if failure == 'capture' else 0)
        assert producer.STATE_KEY not in scope['state']
    asyncio.run(run())


@pytest.mark.parametrize('region', ['US', 'UK'])
@pytest.mark.parametrize('view', ['stock', 'reorder', 'movements'])
def test_minimal_regional_event(monkeypatch, region, view):
    async def run():
        actor, clinic_id = Actor(uuid4(), 'inventoryManager'), uuid4()
        async def resolve(*args):
            return region
        monkeypatch.setattr(producer, 'resolve_view', resolve)
        events = []
        async def sink(body):
            batch = json.loads(body)
            events.extend(batch['events'])
            return TelemetryReceipt(received=len(batch['events']))
        service = incident_producer.IncidentProducer(shared(settings()), queue=ServerQueue(sink=sink))
        monkeypatch.setattr(incident_producer, '_producer', service)
        assert producer.capture_view(actor, clinic_id, view)
        await asyncio.gather(*service.tasks)
        await service.queue.flush()
        assert len(events) == 1
        event = events[0]
        assert event['event_type'] == 'inventory_viewed'
        assert event['properties'] == {'jurisdiction': region, 'environment': 'test', 'view': view}
        assert event['sessionId'] is None and event['requestId'] is None
        assert str(actor.id) not in json.dumps(event) and str(clinic_id) not in json.dumps(event)
        await service.close()
    asyncio.run(run())


@pytest.mark.parametrize('case', ['operator', 'manager', 'regional', 'auditor', 'admin', 'foreign-role',
    'clinic-scope', 'country-scope', 'clinic-missing', 'inactive', 'country-missing', 'country-inactive',
    'region', 'view', 'database'])
def test_context_permissions_and_scope(monkeypatch, case):
    clinic_id, country_id = uuid4(), uuid4()
    role = {'operator': 'inventoryOperator', 'regional': 'inventoryRegional', 'country-scope': 'inventoryRegional',
        'auditor': 'inventoryAuditor', 'admin': 'inventoryAdmin', 'foreign-role': 'admin'}.get(case, 'inventoryManager')
    actor = Actor(uuid4(), role, clinic_ids=() if case == 'clinic-scope' else (clinic_id,),
        jurisdiction_ids=() if case == 'country-scope' else (country_id,))
    class Session:
        async def get(self, model, identity):
            if model is Clinic:
                return None if case == 'clinic-missing' else SimpleNamespace(id=clinic_id,
                    jurisdiction_id=country_id, is_active=case != 'inactive')
            return None if case == 'country-missing' else SimpleNamespace(id=country_id,
                key='ZZ' if case == 'region' else 'US', is_active=case != 'country-inactive')
    @asynccontextmanager
    async def factory():
        yield Session()
    monkeypatch.setattr(producer.database, 'SessionLocal', None if case == 'database' else factory)
    if case in {'operator', 'manager', 'regional', 'auditor'}:
        for view in producer.VIEWS:
            assert asyncio.run(producer.resolve_view(actor, clinic_id, view)) == 'US'
    else:
        with pytest.raises((ValueError, HTTPException)):
            asyncio.run(producer.resolve_view(actor, clinic_id, 'items' if case == 'view' else 'stock'))


@pytest.mark.parametrize('failure', ['lookup', 'timeout', 'cancel'])
def test_failed_preparation_discards(monkeypatch, failure):
    async def run():
        async def resolve(*args):
            if failure == 'lookup':
                raise ValueError('Synthetic private error')
            await asyncio.sleep(10)
        monkeypatch.setattr(producer, 'resolve_view', resolve)
        service = incident_producer.IncidentProducer(settings())
        monkeypatch.setattr(incident_producer, '_producer', service)
        assert producer.capture_view(Actor(uuid4(), 'inventoryManager'), uuid4(), 'stock')
        if failure == 'cancel':
            await asyncio.sleep(0)
            await service.close()
        else:
            await asyncio.gather(*service.tasks)
            assert service.discarded == 1 and not service.queue.pending
            await service.close()
    asyncio.run(run())


def test_optional_marker_limits_and_lifecycle(monkeypatch):
    request = SimpleNamespace(scope={'state': {}})
    actor = Actor(uuid4(), 'inventoryManager')
    producer.mark_view(request, actor, uuid4(), 'items')
    producer.mark_view(request, actor, 'invalid', 'stock')
    assert not request.scope['state']
    producer.mark_view(None, actor, uuid4(), 'stock')
    monkeypatch.setattr(incident_producer, '_producer', None)
    assert not producer.capture_view(actor, uuid4(), 'stock')
    async def run():
        service = incident_producer.IncidentProducer(settings())
        monkeypatch.setattr(incident_producer, '_producer', service)
        assert not producer.capture_view(actor, uuid4(), 'items')
        assert not producer.capture_view(actor, 'invalid', 'stock')
        service.tasks = set(range(16))
        assert not producer.capture_view(actor, uuid4(), 'stock')
        service.tasks.clear()
        await service.close()
        assert not producer.capture_view(actor, uuid4(), 'stock')
    asyncio.run(run())


def test_browser_cannot_assert_view(telemetry):
    from datetime import UTC, datetime
    _, request = telemetry
    context = request('/telemetry/context', {'clinicId': None}).json()
    event = dict(eventId=str(uuid4()), timestamp=datetime.now(UTC).isoformat(), schemaVersion='1.3.0',
        sessionId=context['sessionId'], userId=context['userId'], requestId=None, event_type='inventory_viewed',
        properties=dict(jurisdiction='US', environment='test', view='stock'))
    response = request('/telemetry/events', {'events': [event]}, headers={'X-Telemetry-Context': context['contextToken']})
    assert response.status_code == 403 and response.json()['detail'] == 'Event producer unavailable'


@pytest.mark.integration
def test_postgres_http_views_explicit_clinic_and_empty_reads(monkeypatch):
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy import select
    from httpx import ASGITransport, AsyncClient
    from app.db.session import get_session
    from app.inventory import service as inventory
    from app.inventory.schemas import ItemCreate, ClinicConfig
    from app.reference_data import seed
    from app.main import app
    from app.auth.security import create_access_token
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
            item = await inventory.create_item(session, admin, ItemCreate(title='Synthetic view item',
                product_code='SYN-VIEW-' + str(uuid4()), unit='piece'))
            for clinic in (c1, c2):
                await inventory.configure(session, manager, item.id, clinic.id, ClinicConfig(reorder_point=2))
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
            headers = {'Authorization': 'Bearer ' + create_access_token(manager.id, manager.role, clinic_ids=manager.clinic_ids)}
            async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
                for clinic in (c1, c2):
                    for path in [f'/inventory/items/{item.id}/stock', f'/inventory/items/{item.id}/movements',
                                 '/inventory/stock', '/inventory/reorder']:
                        response = await client.get(path, params={'clinic_id': str(clinic.id)}, headers=headers)
                        assert response.status_code == 200
                        if path.endswith('movements'):
                            assert response.json() == []
                        await asyncio.gather(*service.tasks)
                for path in ['/inventory/stock', '/inventory/reorder']:
                    response = await client.get(path, params={'clinic_id': str(c1.id), 'offset': 100}, headers=headers)
                    assert response.status_code == 200 and response.json() == []
                    await asyncio.gather(*service.tasks)
                for path in ['/inventory/stock', '/inventory/reorder', '/inventory/items']:
                    assert (await client.get(path, headers=headers)).status_code == 200
                assert (await client.get('/inventory/stock')).status_code == 401
                admin_headers = {'Authorization': 'Bearer ' + create_access_token(admin.id, admin.role)}
                assert (await client.get('/inventory/stock', params={'clinic_id': str(c1.id)}, headers=admin_headers)).status_code == 403
                while service.tasks:
                    await asyncio.gather(*service.tasks)
            while service.queue.pending:
                await service.queue.flush()
            views = [event for event in events if event['event_type'] == 'inventory_viewed']
            assert len(views) == 10
            assert {(event['properties']['jurisdiction'], event['properties']['view']) for event in views} == {
                (region, view) for region in ('US', 'UK') for view in producer.VIEWS}
            assert str(item.id) not in json.dumps(views)
        finally:
            if old is None:
                app.dependency_overrides.pop(get_session, None)
            else:
                app.dependency_overrides[get_session] = old
            await service.close()
            await engine.dispose()
    asyncio.run(run())
