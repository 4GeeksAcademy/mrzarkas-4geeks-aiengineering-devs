"""Completed clinic-bound audit reads, byte-preserving ASGI observation and scoped capture."""
import asyncio
import json
from contextlib import asynccontextmanager
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.auth.dependencies import Actor
from app.reference_data.models import Clinic, Jurisdiction
from app.telemetry import inventory_audit_producer as producer, audit_completion as completion, incident_producer
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
                producer.mark_inventory_audit(SimpleNamespace(scope=scope), actor, clinic_id, set())
            for message in messages:
                await send(message)
        async def send(message):
            sent.append(message.copy())
        def capture(*descriptor):
            assert sent == messages
            calls.append(descriptor)
        monkeypatch.setattr(completion, 'capture_inventory_audit', capture)
        scope = {'type': 'http', 'state': {producer.STATE_KEY: ('stale',)}}
        await completion.AuditCompletionMiddleware(app)(scope, None, send)
        assert sent == messages
        assert len(calls) == (1 if marked and status < 300 else 0)
        assert producer.STATE_KEY not in scope['state']
    asyncio.run(run())


@pytest.mark.parametrize('failure', ['send', 'cancel', 'app', 'incomplete', 'capture'])
def test_failed_or_incomplete_delivery_never_becomes_success(monkeypatch, failure):
    async def run():
        calls = []
        async def app(scope, receive, send):
            producer.mark_inventory_audit(SimpleNamespace(scope=scope), Actor(uuid4(), 'inventoryAuditor'), uuid4(), set())
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
        monkeypatch.setattr(completion, 'capture_inventory_audit', capture)
        scope = {'type': 'http', 'state': {}}
        observed = completion.AuditCompletionMiddleware(app)
        if failure in {'send', 'app', 'cancel'}:
            with pytest.raises(asyncio.CancelledError if failure == 'cancel' else RuntimeError):
                await observed(scope, None, send)
        else:
            await observed(scope, None, send)
        assert len(calls) == (1 if failure == 'capture' else 0)
        assert producer.STATE_KEY not in scope['state']
    asyncio.run(run())



@pytest.mark.parametrize('region', ['US', 'UK'])
@pytest.mark.parametrize('failure', [None, 'unknown', 'timeout'])
def test_minimal_regional_capture_and_discard(monkeypatch, region, failure):
    async def run():
        actor, clinic = Actor(uuid4(), 'inventoryAuditor'), uuid4()
        async def resolve(*args):
            if failure == 'unknown': raise ValueError('Unknown synthetic history')
            if failure == 'timeout': await asyncio.sleep(1)
            return region
        monkeypatch.setattr(producer, 'resolve_audit', resolve)
        events = []
        async def sink(body):
            batch = json.loads(body); events.extend(batch['events'])
            return TelemetryReceipt(received=len(batch['events']))
        service = incident_producer.IncidentProducer(shared(settings()), queue=ServerQueue(sink=sink))
        monkeypatch.setattr(incident_producer, '_producer', service)
        assert producer.capture_inventory_audit(actor, clinic, set())
        await asyncio.gather(*service.tasks); await service.queue.flush()
        if failure:
            assert not events and service.discarded == 1
        else:
            assert len(events) == 1
            event = events[0]
            assert event['schemaVersion'] == '1.3.0'
            assert event['properties'] == dict(jurisdiction=region, environment='test', surface='inventory')
            assert event['sessionId'] is None and event['requestId'] is None
            assert str(actor.id) not in json.dumps(events) and str(clinic) not in json.dumps(events)
        await service.close()
    asyncio.run(run())

@pytest.mark.parametrize('case', ['valid', 'empty', 'unknown', 'mixed', 'inactive', 'scope', 'role', 'country-inactive'])
def test_history_comparability_and_permissions(monkeypatch, case):
    clinic, country = uuid4(), uuid4()
    actor = Actor(uuid4(), 'inventoryManager' if case == 'role' else 'inventoryAuditor',
        jurisdiction_ids=() if case == 'scope' else (country,))
    class Session:
        async def get(self, model, identity):
            if model is Clinic:
                return SimpleNamespace(id=clinic, jurisdiction_id=country, is_active=case != 'inactive')
            return SimpleNamespace(id=country, key='US', is_active=case != 'country-inactive')
    @asynccontextmanager
    async def factory(): yield Session()
    monkeypatch.setattr(producer.database, 'SessionLocal', factory)
    countries = set() if case == 'empty' else ({None} if case == 'unknown' else ({country, uuid4()} if case == 'mixed' else {country}))
    if case in {'valid', 'empty'}:
        assert asyncio.run(producer.resolve_audit(actor, clinic, countries)) == 'US'
    else:
        with pytest.raises((ValueError, HTTPException)):
            asyncio.run(producer.resolve_audit(actor, clinic, countries))

def test_previous_contract_version_rejected():
    from datetime import UTC, datetime
    from pydantic import ValidationError
    from app.telemetry.schemas import TelemetryBatch
    event = dict(eventId=str(uuid4()), timestamp=datetime.now(UTC).isoformat(), sessionId=None,
        userId='ps_' + 'a' * 64, requestId=None, schemaVersion='1.3.0', event_type='audit_accessed',
        properties=dict(jurisdiction='US', environment='test', surface='inventory'))
    TelemetryBatch.model_validate({'events': [event]})
    event['schemaVersion'] = '1.2.0'
    with pytest.raises(ValidationError): TelemetryBatch.model_validate({'events': [event]})
@pytest.mark.integration
def test_postgres_http_audits_explicit_clinic_and_empty_reads(monkeypatch):
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
            auditor = Actor(uuid4(), 'inventoryAuditor', jurisdiction_ids=(c1.jurisdiction_id, c2.jurisdiction_id))
            headers = {'Authorization': 'Bearer ' + create_access_token(auditor.id, auditor.role, jurisdiction_ids=auditor.jurisdiction_ids)}
            async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
                for clinic in (c1, c2):
                    for path in [f'/inventory/items/{item.id}/audit', '/inventory/access-denials']:
                        response = await client.get(path, params={'clinic_id': str(clinic.id)}, headers=headers)
                        assert response.status_code == 200
                        await asyncio.gather(*service.tasks)
                response = await client.get(f'/inventory/items/{item.id}/audit', params={'clinic_id': str(c1.id), 'offset': 100}, headers=headers)
                assert response.status_code == 200 and response.json() == []
                await asyncio.gather(*service.tasks)
                assert (await client.get('/inventory/access-denials', headers=headers)).status_code == 200
                assert (await client.get(path, headers=headers)).status_code == 200
                assert (await client.get('/inventory/access-denials')).status_code == 401
                admin_headers = {'Authorization': 'Bearer ' + create_access_token(admin.id, admin.role)}
                assert (await client.get('/inventory/access-denials', params={'clinic_id': str(c1.id)}, headers=admin_headers)).status_code == 403
                while service.tasks:
                    await asyncio.gather(*service.tasks)
            while service.queue.pending:
                await service.queue.flush()
            views = [event for event in events if event['event_type'] == 'audit_accessed']
            assert len(views) == 5
            assert {event['properties']['jurisdiction'] for event in views} == {'US', 'UK'}
            assert all(event['properties']['surface'] == 'inventory' for event in views)
            assert str(item.id) not in json.dumps(views)
        finally:
            if old is None:
                app.dependency_overrides.pop(get_session, None)
            else:
                app.dependency_overrides[get_session] = old
            await service.close()
            await engine.dispose()
    asyncio.run(run())


def test_marker_limits_disabled_closed_and_precedence(monkeypatch):
    from app.telemetry.audit_producer import STATE_KEY as old_key
    actor, clinic = Actor(uuid4(), 'inventoryAuditor'), uuid4()
    request = SimpleNamespace(scope={'state': {}})
    producer.mark_inventory_audit(request, actor, 'invalid', set())
    producer.mark_inventory_audit(request, actor, clinic, set(range(101)))
    producer.mark_inventory_audit(None, actor, clinic, set())
    assert not request.scope['state']
    monkeypatch.setattr(incident_producer, '_producer', None)
    assert not producer.capture_inventory_audit(actor, clinic, set())
    async def run():
        service = incident_producer.IncidentProducer(settings())
        monkeypatch.setattr(incident_producer, '_producer', service)
        service.tasks = set(range(16))
        assert not producer.capture_inventory_audit(actor, clinic, set())
        service.tasks.clear()
        assert not producer.capture_inventory_audit(actor, clinic, set(range(101)))
        await service.close()
        assert not producer.capture_inventory_audit(actor, clinic, set())
        calls = []
        monkeypatch.setattr(completion, 'capture_audit', lambda *args: calls.append('old'))
        monkeypatch.setattr(completion, 'capture_inventory_audit', lambda *args: calls.append('inventory'))
        async def app(scope, receive, send):
            scope['state'][old_key] = (actor, clinic, 'management')
            producer.mark_inventory_audit(SimpleNamespace(scope=scope), actor, clinic, set())
            await send({'type': 'http.response.start', 'status': 200, 'headers': []})
            await send({'type': 'http.response.body', 'body': b'[]'})
        async def send(message): pass
        scope = {'type': 'http'}
        await completion.AuditCompletionMiddleware(app)(scope, None, send)
        assert calls == ['old'] and not scope['state']
    asyncio.run(run())
