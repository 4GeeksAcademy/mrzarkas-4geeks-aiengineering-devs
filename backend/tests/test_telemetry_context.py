import asyncio
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr

from app.auth import security
from app.auth.security import create_access_token
from app.core.config import Settings
from app.main import app
from app.telemetry import router

ACTOR = UUID('00000000-0000-4000-8000-000000000001')


@pytest.fixture
def telemetry(monkeypatch):
    settings = Settings(_env_file=None, app_environment='test', database_url=None,
                        telemetry_enabled=True, telemetry_processing_region='US',
                        telemetry_user_key=SecretStr('u'*32), telemetry_subject_key=SecretStr('s'*32),
                        telemetry_clinic_key=SecretStr('c'*32), telemetry_context_key=SecretStr('t'*32))
    monkeypatch.setattr(router, 'get_settings', lambda: settings)
    monkeypatch.setattr(security, 'get_settings', lambda: settings)
    token = create_access_token(ACTOR, 'technology')
    def request(path, payload=None, headers=None, content=None):
        async def run():
            async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
                options = {'headers': {'Authorization': f'Bearer {token}', **(headers or {})}}
                if content is None:
                    options['json'] = payload
                else:
                    options['content'] = content
                return await client.post(path, **options)
        return asyncio.run(run())
    return settings, request


def test_general_context_hides_operational_identity_and_never_calls_database(telemetry, monkeypatch):
    from app.telemetry import context
    async def forbidden(*args, **kwargs):
        raise AssertionError('General context must not resolve a clinic')
    monkeypatch.setattr(context, 'resolve_clinic', forbidden)
    settings, request = telemetry
    response = request('/telemetry/context', {'clinicId': None})
    assert response.status_code == 200
    data = response.json()
    assert set(data) == {'contextToken', 'sessionId', 'userId', 'jurisdiction', 'schemaVersion', 'expiresAt'}
    assert data['jurisdiction'] is None
    assert response.headers['cache-control'] == 'no-store'
    assert data['userId'].startswith('ps_') and len(data['userId']) == 67
    import jwt
    claims = jwt.decode(data['contextToken'], options={'verify_signature': False})
    assert str(ACTOR) not in str(claims)
    assert 'sub' not in claims and 'clinicId' not in claims
    for key in [settings.telemetry_user_key, settings.telemetry_context_key]:
        assert key.get_secret_value() not in response.text


def test_context_requires_authentication_and_closed_payload(telemetry):
    _, request = telemetry
    unauthenticated = request('/telemetry/context', {'clinicId': None}, {'Authorization': ''})
    assert unauthenticated.status_code == 401
    assert unauthenticated.headers['cache-control'] == 'no-store'
    assert request('/telemetry/context', {}).status_code == 422
    response = request('/telemetry/context', {'clinicId': 'synthetic-sensitive-value'})
    assert response.status_code == 422 and 'synthetic-sensitive-value' not in response.text
    assert request('/telemetry/context', {'clinicId': None, 'region': 'UK'}).status_code == 422


def test_disabled_missing_keys_and_staging_fail_closed(telemetry):
    settings, request = telemetry
    for field, value in [('telemetry_enabled', False), ('telemetry_user_key', None),
                         ('telemetry_processing_region', None), ('app_environment', 'staging')]:
        old = getattr(settings, field)
        setattr(settings, field, value)
        assert request('/telemetry/context', {'clinicId': None}).status_code == 503
        setattr(settings, field, old)


def test_renewal_keeps_sid_and_invalid_previous_is_rejected(telemetry):
    _, request = telemetry
    first = request('/telemetry/context', {'clinicId': None}).json()
    renewed = request('/telemetry/context', {'clinicId': None}, {'X-Telemetry-Context': first['contextToken']})
    assert renewed.status_code == 200 and renewed.json()['sessionId'] == first['sessionId']
    assert request('/telemetry/context', {'clinicId': None}, {'X-Telemetry-Context': 'bad'}).status_code == 401


def test_clinic_context_uses_server_resolution(telemetry, monkeypatch):
    from app.telemetry import context
    seen = []
    async def resolve(settings, actor, clinic_id=None, binding=None):
        seen.append((actor.id, clinic_id))
        return 'b'*64, 'US'
    monkeypatch.setattr(context, 'resolve_clinic', resolve)
    _, request = telemetry
    assert request('/telemetry/context', {'clinicId': str(ACTOR)}).json()['jurisdiction'] == 'US'
    assert seen == [(ACTOR, ACTOR)]


@pytest.mark.parametrize('case', ['valid', 'inactive', 'unknown-region', 'foreign-region', 'missing', 'denied'])
def test_real_resolver_reads_clinic_region_and_denies_invalid_contexts(telemetry, monkeypatch, case):
    from contextlib import asynccontextmanager
    from app.telemetry.context import resolve_clinic
    from app.db import session
    from app.auth.dependencies import Actor
    from fastapi import HTTPException
    settings, _ = telemetry
    rows = [] if case == 'missing' else [(ACTOR, case != 'inactive', 'ZZ' if case == 'unknown-region' else ('UK' if case == 'foreign-region' else 'US'), True)]
    class Result:
        def __aiter__(self):
            async def iterate():
                for row in rows: yield row
            return iterate()
    class Session:
        async def stream(self, statement):
            assert str(statement).startswith('SELECT')
            return Result()
    @asynccontextmanager
    async def factory():
        yield Session()
    monkeypatch.setattr(session, 'SessionLocal', factory)
    actor = Actor(ACTOR, 'direction' if case == 'denied' else 'technology')
    if case == 'valid':
        assert asyncio.run(resolve_clinic(settings, actor, clinic_id=ACTOR))[1] == 'US'
    else:
        with pytest.raises(HTTPException) as error:
            asyncio.run(resolve_clinic(settings, actor, clinic_id=ACTOR))
        assert error.value.status_code == {'inactive':422, 'unknown-region':422, 'foreign-region':403, 'missing':404, 'denied':404}[case]
