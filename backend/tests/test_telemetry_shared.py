"""A single API resolves both clinical regions; browser declarations never select keys."""
import asyncio
import json
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from uuid import UUID, uuid4

import jwt
import pytest
from pydantic import SecretStr
from fastapi import HTTPException

from test_telemetry_context import telemetry, ACTOR
from app.auth.dependencies import Actor
from app.telemetry import context, incident_producer
from app.telemetry.identity import ConfigurationError, ContextError, keys, region_settings, user_id, decode_context
from app.telemetry.server import ServerQueue
from app.telemetry.schemas import TelemetryReceipt

US = UUID('00000000-0000-0000-0000-000000000101')
UK = UUID('00000000-0000-0000-0000-000000000102')


def shared(settings):
    settings.telemetry_processing_region = None
    for region in ('us', 'uk'):
        for purpose in ('user', 'subject', 'clinic', 'context', 'resource'):
            setattr(settings, f'telemetry_{region}_{purpose}_key', SecretStr(f'synthetic-{region}-{purpose}-' + 'x'*32))
    return settings


def clinic_database(monkeypatch):
    from app.db import session
    rows = [(US, True, 'US', True), (UK, True, 'UK', True)]
    class Result:
        def __aiter__(self):
            async def iterate():
                for row in rows: yield row
            return iterate()
    class Session:
        async def stream(self, statement): return Result()
    @asynccontextmanager
    async def factory(): yield Session()
    monkeypatch.setattr(session, 'SessionLocal', factory)
    return rows


def envelope(ctx, region):
    return dict(eventId=str(uuid4()), timestamp=datetime.now(UTC).isoformat(),
                sessionId=ctx['sessionId'], userId=ctx['userId'], event_type='navigation_viewed',
                schemaVersion='1.2.0', requestId=None,
                properties=dict(jurisdiction=region, environment='test', view='incident_detail'))


def test_one_api_accepts_both_regions_and_revalidates_clinics(telemetry, monkeypatch):
    settings, request = telemetry
    shared(settings)
    rows = clinic_database(monkeypatch)
    scopes = {}
    for identity, region in [(US, 'US'), (UK, 'UK')]:
        response = request('/telemetry/context', {'clinicId': str(identity)})
        assert response.status_code == 200
        ctx = response.json(); scopes[region] = ctx
        assert ctx['jurisdiction'] == region
        assert ctx['userId'] == user_id(region_settings(settings, region), ACTOR)
        headers = {'X-Telemetry-Context': ctx['contextToken']}
        assert request('/telemetry/events', {'events': [envelope(ctx, region)]}, headers).status_code == 200
        assert str(identity) not in response.text and str(ACTOR) not in response.text
    assert scopes['US']['userId'] != scopes['UK']['userId']
    assert request('/telemetry/events', {'events': [envelope(scopes['US'], 'UK')]},
                   {'X-Telemetry-Context': scopes['US']['contextToken']}).status_code == 403
    rows[1] = (UK, False, 'UK', True)
    assert request('/telemetry/events', {'events': [envelope(scopes['UK'], 'UK')]},
                   {'X-Telemetry-Context': scopes['UK']['contextToken']}).status_code == 422


def test_shared_general_scope_and_switch_preserve_session_not_identity(telemetry, monkeypatch):
    settings, request = telemetry
    shared(settings); clinic_database(monkeypatch)
    general = request('/telemetry/context', {'clinicId': None}).json()
    assert general['jurisdiction'] is None
    assert decode_context(settings, general['contextToken'], Actor(ACTOR, 'technology'))['processingRegion'] is None
    previous = general
    for identity, region in [(US, 'US'), (UK, 'UK')]:
        current = request('/telemetry/context', {'clinicId': str(identity)},
                          {'X-Telemetry-Context': previous['contextToken']}).json()
        assert current['sessionId'] == general['sessionId'] and current['userId'] != previous['userId']
        assert current['jurisdiction'] == region
        previous = current
    assert request('/telemetry/context', {'clinicId': str(US), 'region': 'UK'}).status_code == 422


def test_shared_selector_cannot_override_signature_or_jurisdiction(telemetry, monkeypatch):
    settings, request = telemetry
    shared(settings); clinic_database(monkeypatch)
    token = request('/telemetry/context', {'clinicId': str(US)}).json()['contextToken']
    claims = jwt.decode(token, options={'verify_signature': False})
    for selector in ['UK', 'GENERAL', 'INVALID']:
        forged = jwt.encode(claims, settings.telemetry_us_context_key.get_secret_value(), algorithm='HS256',
                            headers={'kid': 'v1', 'region': selector})
        with pytest.raises(ContextError): decode_context(settings, forged, Actor(ACTOR, 'technology'))
    claims['jurisdiction'] = 'UK'
    forged = jwt.encode(claims, settings.telemetry_us_context_key.get_secret_value(), algorithm='HS256',
                        headers={'kid': 'v1', 'region': 'US'})
    with pytest.raises(ContextError): decode_context(settings, forged, Actor(ACTOR, 'technology'))


@pytest.mark.parametrize('case', ['missing', 'reused', 'short', 'jwt', 'endpoint'])
def test_shared_keyrings_fail_closed(telemetry, case):
    settings, _ = telemetry
    shared(settings)
    if case == 'missing': settings.telemetry_uk_context_key = None
    if case == 'reused': settings.telemetry_uk_user_key = settings.telemetry_us_user_key
    if case == 'short': settings.telemetry_us_resource_key = SecretStr('short')
    if case == 'jwt': settings.telemetry_uk_context_key = settings.jwt_secret_key
    if case == 'endpoint': settings.telemetry_uk_endpoint = 'https://host/wrong'
    with pytest.raises(ConfigurationError): keys(settings)


def test_shared_incident_producer_selects_regional_resource_keys_and_batches(telemetry, monkeypatch):
    settings, _ = telemetry
    shared(settings); clinic_database(monkeypatch)
    async def run():
        batches = []
        async def sink(body):
            batch = json.loads(body); batches.append(batch)
            return TelemetryReceipt(received=len(batch['events']))
        service = incident_producer.IncidentProducer(settings, queue=ServerQueue(sink=sink))
        actor = Actor(ACTOR, 'technology'); incident, audit = uuid4(), uuid4()
        for clinic in [US, UK]: assert service.capture('incident_created', actor, clinic, incident, audit)
        await asyncio.gather(*service.tasks)
        await service.queue.flush(); await service.queue.flush()
        assert len(batches) == 2
        events = [batch['events'][0] for batch in batches]
        assert {e['properties']['jurisdiction'] for e in events} == {'US', 'UK'}
        assert events[0]['userId'] != events[1]['userId']
        assert events[0]['properties']['incidentId'] != events[1]['properties']['incidentId']
        assert events[0]['properties']['auditId'] != events[1]['properties']['auditId']
        assert str(incident) not in json.dumps(batches)
        await service.close()
    asyncio.run(run())


@pytest.mark.integration
def test_shared_postgresql_contexts_and_server_producer(telemetry, monkeypatch):
    from app.core.config import get_settings
    config = get_settings()
    if config.database_url is None or not config.require_database_url().endswith('/telemetry_validation'):
        pytest.skip('Dedicated synthetic telemetry_validation database required')
    settings, request = telemetry
    shared(settings)
    for identity, region in [(US, 'US'), (UK, 'UK')]:
        response = request('/telemetry/context', {'clinicId': str(identity)})
        assert response.status_code == 200
        ctx = response.json(); assert ctx['jurisdiction'] == region
        assert request('/telemetry/events', {'events': [envelope(ctx, region)]},
                       {'X-Telemetry-Context': ctx['contextToken']}).status_code == 200
    async def run():
        service = incident_producer.IncidentProducer(settings)
        actor = Actor(ACTOR, 'technology')
        for clinic in [US, UK]: assert service.capture('incident_created', actor, clinic, uuid4(), uuid4())
        await asyncio.gather(*service.tasks)
        events = [json.loads(entry[2]) for entry in service.queue.pending]
        assert {e['properties']['jurisdiction'] for e in events} == {'US', 'UK'}
        assert len({e['userId'] for e in events}) == 2
        await service.close()
    asyncio.run(run())
