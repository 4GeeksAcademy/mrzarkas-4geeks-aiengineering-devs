import pytest
import jwt

from test_telemetry_context import telemetry, ACTOR
from app.auth.dependencies import Actor
from app.telemetry.identity import user_id, subject_binding, clinic_binding, decode_context, ContextError, ConfigurationError
from pydantic import SecretStr


def test_hmac_is_stable_and_separated_by_purpose_and_key(telemetry):
    settings, _ = telemetry
    first = user_id(settings, ACTOR)
    assert first == user_id(settings, ACTOR)
    assert first[3:] != subject_binding(settings, ACTOR)
    assert subject_binding(settings, ACTOR) != clinic_binding(settings, ACTOR)
    settings.telemetry_user_key = SecretStr('z'*32)
    assert user_id(settings, ACTOR) != first


def test_shared_or_login_keys_are_refused(telemetry):
    settings, _ = telemetry
    settings.telemetry_subject_key = settings.telemetry_user_key
    with pytest.raises(ConfigurationError): user_id(settings, ACTOR)


@pytest.mark.parametrize('change', ['actor', 'region', 'expiry', 'audience', 'key-version', 'signature'])
def test_context_forgery_and_cross_scope_are_rejected(telemetry, change):
    settings, request = telemetry
    token = request('/telemetry/context', {'clinicId': None}).json()['contextToken']
    claims = jwt.decode(token, options={'verify_signature': False})
    actor = Actor(ACTOR, 'technology')
    if change == 'actor':
        from uuid import UUID
        actor = Actor(UUID('00000000-0000-4000-8000-000000000002'), 'technology')
    if change == 'region': claims['processingRegion'] = 'UK'
    if change == 'expiry': claims['exp'] = 1
    if change == 'audience': claims['aud'] = 'other'
    if change == 'key-version': claims['pseudonymVersion'] = 'other'
    if change != 'actor':
        token = jwt.encode(claims, 'q'*32 if change == 'signature' else settings.telemetry_context_key.get_secret_value(), algorithm='HS256', headers={'kid': settings.telemetry_key_version})
    with pytest.raises(ContextError): decode_context(settings, token, actor)


@pytest.mark.parametrize('endpoint', ['http://localhost:8000/telemetry/events', 'https://regional.example/telemetry/events'])
def test_receiver_reference_is_configurable_without_changing_route(telemetry, endpoint):
    settings, request = telemetry
    settings.telemetry_endpoint = endpoint
    assert request('/telemetry/context', {'clinicId': None}).status_code == 200


@pytest.mark.parametrize('endpoint', ['http://user:secret@host/telemetry/events', 'https://host/wrong', 'https://host/telemetry/events?token=secret', 'not-a-url'])
def test_invalid_receiver_reference_fails_closed(telemetry, endpoint):
    settings, request = telemetry
    settings.telemetry_endpoint = endpoint
    response = request('/telemetry/context', {'clinicId': None})
    assert response.status_code == 503 and endpoint not in response.text
