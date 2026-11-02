import copy
import json
import logging
from pathlib import Path

import pytest

from test_telemetry_context import telemetry, ACTOR
from app.telemetry.schemas import TelemetryBatch, EVENT_MODELS, CONTRACT
from pydantic import ValidationError


def event(context):
    return {'eventId': str(ACTOR), 'timestamp': '2026-11-01T10:00:00Z',
            'sessionId': context['sessionId'], 'userId': context['userId'],
            'event_type': 'navigation_viewed', 'schemaVersion': '1.3.0', 'requestId': None,
            'properties': {'jurisdiction': None, 'environment': 'test', 'view': 'management'}}


def test_batch_acknowledges_count_with_safe_log_and_no_database(telemetry, caplog, monkeypatch):
    from app.db import session
    def forbidden():
        raise AssertionError('No database session allowed')
    monkeypatch.setattr(session, 'SessionLocal', forbidden)
    _, request = telemetry
    context = request('/telemetry/context', {'clinicId': None}).json()
    with caplog.at_level(logging.INFO, logger='healthcore.telemetry'):
        response = request('/telemetry/events', {'events': [event(context)]*20}, {'X-Telemetry-Context': context['contextToken']})
    assert response.status_code == 200 and response.json() == {'received': 20}
    assert 'count=20' in caplog.text and 'navigation_viewed' in caplog.text
    assert context['userId'] not in caplog.text and context['contextToken'] not in caplog.text


@pytest.mark.parametrize('mutation', ['empty', 'over-count', 'extra', 'secret', 'invalid-date', 'nan'])
def test_invalid_batch_is_atomic_and_does_not_reflect_input(telemetry, mutation):
    _, request = telemetry
    ctx = request('/telemetry/context', {'clinicId': None}).json()
    value = event(ctx)
    batch = {'events': [value]}
    if mutation == 'empty': batch['events'] = []
    if mutation == 'over-count': batch['events'] *= 21
    if mutation == 'extra': batch['secret'] = 'synthetic-sensitive-value'
    if mutation == 'secret': value['properties']['email'] = 'synthetic-sensitive-value'
    if mutation == 'invalid-date': value['timestamp'] = '2026-02-30T10:00:00Z'
    if mutation == 'nan': value['properties']['jurisdiction'] = float('nan')
    # Send explicit JSON to exercise parser including non-standard NaN rejection.
    response = request('/telemetry/events', headers={'X-Telemetry-Context': ctx['contextToken'], 'Content-Type': 'application/json'}, content=json.dumps(batch))
    assert response.status_code == 422
    assert 'synthetic-sensitive-value' not in response.text


@pytest.mark.parametrize('field', ['userId', 'sessionId', 'jurisdiction', 'environment'])
def test_context_mismatch_rejects_whole_batch(telemetry, field):
    _, request = telemetry
    ctx = request('/telemetry/context', {'clinicId': None}).json()
    valid = event(ctx); wrong = copy.deepcopy(valid)
    if field == 'userId': wrong[field] = 'ps_'+'a'*64
    elif field == 'sessionId': wrong[field] = '00000000-0000-4000-8000-000000000002'
    else: wrong['properties'][field] = 'UK' if field == 'jurisdiction' else 'production'
    response = request('/telemetry/events', {'events': [valid, wrong]}, {'X-Telemetry-Context': ctx['contextToken']})
    assert response.status_code == 403


def test_body_size_checked_even_without_content_length(telemetry):
    _, request = telemetry
    response = request('/telemetry/events', content=b'x'*(48*1024+1))
    assert response.status_code == 413
    assert 'x'*100 not in response.text


def test_packaged_schema_matches_single_source():
    source = Path(__file__).resolve().parents[2] / 'docs/telemetry/event-schemas.json'
    # Container test image does not copy monorepo docs; assert parity on the host in delivery.
    if source.exists(): assert CONTRACT == json.loads(source.read_text())
    assert len(EVENT_MODELS) == 39
    with pytest.raises(ValidationError):
        TelemetryBatch.model_validate({'events': []})


def test_telemetry_openapi_exposes_typed_input_success_and_safe_errors():
    from app.main import app
    paths = app.openapi()['paths']
    for path in ['/telemetry/context', '/telemetry/events']:
        operation = paths[path]['post']
        assert operation['requestBody']['required']
        assert {'200', '401', '403', '413', '422', '503'} <= set(operation['responses'])


def sample(schema):
    if 'enum' in schema: return schema['enum'][0]
    if 'const' in schema: return schema['const']
    if 'anyOf' in schema: return sample(schema['anyOf'][0])
    if schema.get('type') in {'number', 'integer'}: return schema.get('minimum', 0)
    if schema.get('format') == 'date-time': return '2026-11-01T10:00:00Z'
    if 'ps_' in schema.get('pattern', ''): return 'ps_'+'a'*64
    return str(ACTOR)


@pytest.mark.parametrize('name', sorted(EVENT_MODELS))
def test_every_contract_model_checks_required_extras_nullable_and_dates(name):
    definition = CONTRACT['definitions'][name]['allOf'][1]['properties']['properties']
    value = {'eventId': str(ACTOR), 'timestamp': '2026-11-01T10:00:00Z', 'sessionId': None,
             'userId': None, 'event_type': name, 'schemaVersion': '1.3.0', 'requestId': None,
             'properties': {key: sample(schema) for key, schema in definition['properties'].items()}}
    model = EVENT_MODELS[name]
    model.model_validate(value)
    for key in definition['required']:
        invalid = copy.deepcopy(value); del invalid['properties'][key]
        with pytest.raises(ValidationError): model.model_validate(invalid)
    invalid = copy.deepcopy(value); invalid['properties']['unknown'] = 'synthetic'
    with pytest.raises(ValidationError): model.model_validate(invalid)
    invalid = copy.deepcopy(value); invalid['timestamp'] = '2026-02-30T10:00:00Z'
    with pytest.raises(ValidationError): model.model_validate(invalid)
    value['properties']['jurisdiction'] = None
    if None in definition['properties']['jurisdiction'].get('enum', []):
        model.model_validate(value)
    else:
        with pytest.raises(ValidationError): model.model_validate(value)


def test_chunked_body_is_limited_before_json_parsing(telemetry):
    import asyncio
    from httpx import ASGITransport, AsyncClient
    from app.main import app
    async def content():
        for _ in range(50): yield b'x'*1024
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
            return await client.post('/telemetry/events', content=content())
    response = asyncio.run(run())
    assert response.status_code == 413
    assert 'content-length' not in response.request.headers


@pytest.mark.parametrize('origin, expected', [('http://localhost:8080', 200), ('https://untrusted.example', 400)])
def test_context_header_cors_preserves_origin_allowlist(telemetry, origin, expected):
    import asyncio
    from httpx import ASGITransport, AsyncClient
    from app.main import app
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
            return await client.options('/telemetry/events', headers={
                'Origin': origin, 'Access-Control-Request-Method':'POST',
                'Access-Control-Request-Headers':'authorization,content-type,x-telemetry-context'})
    response = asyncio.run(run())
    assert response.status_code == expected
    if expected == 200: assert response.headers['access-control-allow-origin'] == origin
    else: assert 'access-control-allow-origin' not in response.headers


def test_nullable_scope_does_not_grant_browser_producer_admission():
    from app.telemetry.schemas import GENERAL_EVENTS, NULLABLE_EVENTS, VERSION
    added = {'authentication_succeeded', 'authentication_failed', 'authorization_denied',
             'api_request_completed', 'catalog_cache_observed', 'service_health_checked',
             'data_integrity_checked', 'telemetry_contract_rejected', 'telemetry_delivery_failed'}
    assert VERSION == '1.3.0'
    assert NULLABLE_EVENTS == GENERAL_EVENTS | added
    assert len(GENERAL_EVENTS) == 5
    assert not ({'audit_accessed', 'management_mutation_completed', 'incident_created'} & NULLABLE_EVENTS)


@pytest.mark.parametrize('name', ['authentication_succeeded', 'authentication_failed', 'authorization_denied',
                                  'api_request_completed', 'catalog_cache_observed', 'service_health_checked',
                                  'data_integrity_checked', 'telemetry_contract_rejected', 'telemetry_delivery_failed'])
def test_general_server_contract_still_rejected_at_browser_ingress(telemetry, name):
    _, request = telemetry
    ctx = request('/telemetry/context', {'clinicId': None}).json()
    definition = CONTRACT['definitions'][name]['allOf'][1]['properties']['properties']
    value = event(ctx)
    value['event_type'] = name
    value['properties'] = {key: sample(schema) for key, schema in definition['properties'].items()}
    value['properties'].update(jurisdiction=None, environment='test')
    EVENT_MODELS[name].model_validate(value)
    response = request('/telemetry/events', {'events': [value]}, {'X-Telemetry-Context': ctx['contextToken']})
    assert response.status_code == 403 and response.json() == {'detail': 'Event producer unavailable'}


def test_previous_schema_version_is_not_silently_normalized(telemetry):
    _, request = telemetry
    ctx = request('/telemetry/context', {'clinicId': None}).json()
    assert ctx['schemaVersion'] == '1.3.0'
    value = event(ctx); value['schemaVersion'] = '1.1.0'
    response = request('/telemetry/events', {'events': [value]}, {'X-Telemetry-Context': ctx['contextToken']})
    assert response.status_code == 422
