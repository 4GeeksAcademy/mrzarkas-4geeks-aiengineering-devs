"""Synthetic UI flow identity, ingress and regional scopes."""
import asyncio
import json
from contextlib import asynccontextmanager
from types import SimpleNamespace
from uuid import uuid4

import jwt
import pytest
from fastapi import HTTPException

from app.auth.dependencies import Actor
from app.telemetry import inventory_flow_identity as identity, inventory_flow_router as router, incident_producer
from app.telemetry.identity import region_settings, keys, now_seconds, ContextError
from app.telemetry.schemas import TelemetryReceipt
from app.telemetry.server import ServerQueue
from app.inventory.models import InventoryItem, InventoryClinicItem
from app.reference_data.models import Clinic, Jurisdiction
from test_telemetry_incident_producer import settings
from test_telemetry_shared import shared
from test_telemetry_context import telemetry


@pytest.mark.parametrize('region', ['US', 'UK'])
def test_flow_credentials_bound_and_do_not_extend(region):
    config = region_settings(shared(settings()), region)
    actor = Actor(uuid4(), 'inventoryManager')
    clinic, item = uuid4(), uuid4()
    expiry = now_seconds() + 60
    flow, token, exp = identity.issue_flow(config, actor, clinic, item, None, expiry)
    started, token2, exp2 = identity.issue_flow(config, actor, clinic, item, 'outbound', expiry + 30, token)
    assert flow == started and exp == exp2 == expiry
    assert str(clinic) not in token and str(item) not in token
    claims = jwt.decode(token2, keys(config)[3], algorithms=['HS256'], audience=identity.AUDIENCE)
    assert set(claims) == identity.FIELDS and claims['direction'] == 'outbound'
    assert all(str(value) not in json.dumps(claims) for value in [actor.id, clinic, item])
    other_region = region_settings(shared(settings()), 'UK' if region == 'US' else 'US')
    for observed, c, i, direction, cred, cfg in [
        (Actor(uuid4(), 'inventoryManager'), clinic, item, 'outbound', token2, config),
        (actor, uuid4(), item, 'outbound', token2, config),
        (actor, clinic, uuid4(), 'outbound', token2, config),
        (actor, clinic, item, 'inbound', token2, config),
        (actor, clinic, item, 'outbound', token2, other_region),
        (actor, clinic, item, 'outbound', token2 + 'tamper', config),
    ]:
        with pytest.raises(ContextError):
            identity.issue_flow(cfg, observed, c, i, direction, expiry, cred)
    claims['exp'] = now_seconds() - 1
    expired = jwt.encode(claims, keys(config)[3], algorithm='HS256', headers={'kid': config.telemetry_key_version, 'region': region})
    with pytest.raises(ContextError):
        identity.issue_flow(config, actor, clinic, item, 'outbound', expiry, expired)


@pytest.mark.parametrize('case', ['valid', 'regional-selection', 'operator-start', 'admin', 'scope', 'regional-start',
    'clinic-missing', 'clinic-inactive', 'country-missing', 'country-inactive', 'region', 'item-missing', 'item-inactive', 'config-missing'])
def test_resource_scope(monkeypatch, case):
    clinic, country, item = uuid4(), uuid4(), uuid4()
    role = 'inventoryRegional' if case.startswith('regional') else 'inventoryOperator' if case == 'operator-start' else 'inventoryAdmin' if case == 'admin' else 'inventoryManager'
    actor = Actor(uuid4(), role, clinic_ids=() if case == 'scope' else (clinic,), jurisdiction_ids=(country,))
    action = 'product_selected' if case == 'regional-selection' else 'order_started'
    class Session:
        async def get(self, model, value):
            return {Clinic: None if case == 'clinic-missing' else SimpleNamespace(id=clinic, jurisdiction_id=country, is_active=case != 'clinic-inactive'),
                Jurisdiction: None if case == 'country-missing' else SimpleNamespace(id=country, key='ZZ' if case == 'region' else 'US', is_active=case != 'country-inactive'),
                InventoryItem: None if case == 'item-missing' else SimpleNamespace(id=item, is_active=case != 'item-inactive'),
                InventoryClinicItem: None if case == 'config-missing' else object()}[model]
    @asynccontextmanager
    async def factory():
        yield Session()
    monkeypatch.setattr(identity.database, 'SessionLocal', factory)
    if case in {'valid', 'regional-selection', 'operator-start'}:
        assert asyncio.run(identity.resolve_flow(actor, clinic, item, action)) == 'US'
    else:
        with pytest.raises((ValueError, HTTPException)):
            asyncio.run(identity.resolve_flow(actor, clinic, item, action))


def test_ingress_and_existing_browser_rejection(telemetry, monkeypatch):
    from datetime import UTC, datetime
    config, request = telemetry
    config.telemetry_resource_key = settings().telemetry_resource_key
    async def resolve(*args):
        return 'US'
    monkeypatch.setattr(router, 'resolve_flow', resolve)
    async def recorded(*args): return True
    monkeypatch.setattr(router, 'record', recorded)
    class Queue:
        def __init__(self): self.events = []
        def enqueue(self, event, scope): self.events.append(event); return True
    service = SimpleNamespace(settings=config, closed=False, queue=Queue())
    monkeypatch.setattr(incident_producer, '_producer', service)
    clinic, item = uuid4(), uuid4()
    payload = dict(action='product_selected', clinicId=str(clinic), itemId=str(item))
    response = request('/telemetry/inventory-flow', payload)
    assert response.status_code == 200 and response.headers['cache-control'] == 'no-store'
    selected = response.json()
    assert set(selected) == {'accepted', 'flowId', 'flowToken', 'expiresAt'}
    start = request('/telemetry/inventory-flow', dict(payload, action='order_started', direction='inbound', flowToken=selected['flowToken']))
    assert start.status_code == 200 and start.json()['flowId'] == selected['flowId']
    assert [event['event_type'] for event in service.queue.events] == ['product_selected', 'order_started']
    assert service.flow_preparations == 0
    assert request('/telemetry/inventory-flow', dict(payload, extra='forbidden')).status_code == 422
    assert request('/telemetry/inventory-flow', dict(payload, action='order_started')).status_code == 422
    assert request('/telemetry/inventory-flow', dict(payload, direction='inbound')).status_code == 422
    assert request('/telemetry/inventory-flow', dict(payload, flowToken='tampered')).status_code == 401
    service.flow_preparations = 16
    assert request('/telemetry/inventory-flow', payload).status_code == 503
    service.flow_preparations = 0
    context = request('/telemetry/context', {'clinicId': None}).json()
    for value in service.queue.events:
        event = dict(value, sessionId=context['sessionId'], userId=context['userId'])
        result = request('/telemetry/events', {'events': [event]}, headers={'X-Telemetry-Context': context['contextToken']})
        assert result.status_code == 403 and result.json()['detail'] == 'Event producer unavailable'
    monkeypatch.setattr(incident_producer, '_producer', None)
    assert request('/telemetry/inventory-flow', payload).status_code == 503


@pytest.mark.integration
def test_postgres_flow_ingress_both_regions(monkeypatch):
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from httpx import ASGITransport, AsyncClient
    from app.reference_data import seed
    from app.inventory import service as inventory
    from app.inventory.schemas import ItemCreate, ClinicConfig
    from app.auth.security import create_access_token
    from app.main import app
    from test_inventory import isolated_url, setup_fixture

    async def run():
        engine = create_async_engine(isolated_url())
        factory = async_sessionmaker(engine, expire_on_commit=False)
        monkeypatch.setattr(seed, 'SessionLocal', factory)
        monkeypatch.setattr(identity.database, 'SessionLocal', factory)
        await seed.seed_reference_data()
        async with factory() as session, session.begin():
            c1, c2, admin, _, _ = await setup_fixture(session)
            for clinic, region in [(c1, 'US'), (c2, 'UK')]:
                clinic.jurisdiction_id = (await session.scalar(select(Jurisdiction).where(Jurisdiction.key == region))).id
            actor = Actor(uuid4(), 'inventoryManager', clinic_ids=(c1.id, c2.id))
            item = await inventory.create_item(session, admin, ItemCreate(title='Synthetic flow', product_code='SYN-FLOW-' + str(uuid4()), unit='piece'))
            for clinic in (c1, c2):
                await inventory.configure(session, actor, item.id, clinic.id, ClinicConfig(reorder_point=2))
        events = []
        async def sink(body):
            batch = json.loads(body); events.extend(batch['events'])
            return TelemetryReceipt(received=len(batch['events']))
        service = incident_producer.IncidentProducer(shared(settings()), queue=ServerQueue(sink=sink))
        monkeypatch.setattr(incident_producer, '_producer', service)
        try:
            headers = {'Authorization': 'Bearer ' + create_access_token(actor.id, actor.role, clinic_ids=actor.clinic_ids)}
            async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
                for clinic in (c1, c2):
                    payload = dict(action='product_selected', clinicId=str(clinic.id), itemId=str(item.id))
                    response = await client.post('/telemetry/inventory-flow', headers=headers, json=payload)
                    assert response.status_code == 200
                    selection = response.json()
                    response = await client.post('/telemetry/inventory-flow', headers=headers,
                        json=dict(payload, action='order_started', direction='outbound', flowToken=selection['flowToken']))
                    assert response.status_code == 200 and response.json()['flowId'] == selection['flowId']
                assert (await client.post('/telemetry/inventory-flow', json=payload)).status_code == 401
                restricted = {'Authorization': 'Bearer ' + create_access_token(actor.id, actor.role, clinic_ids=(c1.id,))}
                assert (await client.post('/telemetry/inventory-flow', headers=restricted, json=payload)).status_code == 403
                while service.tasks:
                    await asyncio.gather(*service.tasks)
            while service.queue.pending:
                await service.queue.flush()
            gestures = [event for event in events if event['event_type'] in {'product_selected', 'order_started'}]
            assert len(gestures) == 4
            assert {(event['event_type'], event['properties']['jurisdiction']) for event in gestures} == {
                (action, region) for action in ('product_selected', 'order_started') for region in ('US', 'UK')}
            assert str(item.id) not in json.dumps(gestures)
        finally:
            await service.close(); await engine.dispose()
    asyncio.run(run())
