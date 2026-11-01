"""Purpose-separated HMAC and short-lived, signed context credentials."""
import hashlib
import hmac
from datetime import UTC, datetime
from uuid import UUID
from urllib.parse import urlsplit

import jwt

from app.core.config import Settings

ISSUER = 'healthcore-telemetry'
AUDIENCE = 'healthcore-telemetry-events'


class ContextError(ValueError):
    pass


class ConfigurationError(ValueError):
    pass


def keys(settings: Settings):
    values = [settings.telemetry_user_key, settings.telemetry_subject_key,
              settings.telemetry_clinic_key, settings.telemetry_context_key]
    if (not settings.telemetry_enabled
            or settings.app_environment not in {'development', 'test', 'production'}
            or not 1 <= settings.telemetry_context_ttl_seconds <= 300):
        raise ConfigurationError('Telemetry unavailable')
    if settings.telemetry_endpoint:
        target = urlsplit(settings.telemetry_endpoint)
        if (target.scheme not in {'http', 'https'} or not target.hostname
                or target.username is not None or target.password is not None
                or target.path != '/telemetry/events' or target.query or target.fragment
                or (settings.app_environment == 'production' and target.scheme != 'https')):
            raise ConfigurationError('Telemetry unavailable')
    if any(value is None or len(value.get_secret_value().encode()) < 32 for value in values):
        raise ConfigurationError('Telemetry unavailable')
    decoded = [value.get_secret_value() for value in values]
    if len(set(decoded)) != 4 or settings.jwt_secret_key.get_secret_value() in decoded:
        raise ConfigurationError('Telemetry unavailable')
    if settings.telemetry_processing_region is None:
        # A shared backend requires independent clinical keyrings. General events
        # retain their own keys and null jurisdiction; no invented clinic/region.
        all_values = list(decoded)
        for region in ('us', 'uk'):
            for purpose in ('user', 'subject', 'clinic', 'context', 'resource'):
                secret = getattr(settings, f'telemetry_{region}_{purpose}_key')
                if secret is None:
                    if purpose == 'resource':
                        continue  # Browser ingress can operate without incident producers.
                    raise ConfigurationError('Telemetry unavailable')
                value = secret.get_secret_value()
                if len(value.encode()) < 32:
                    raise ConfigurationError('Telemetry unavailable')
                all_values.append(value)
            validate_endpoint(settings, getattr(settings, f'telemetry_{region}_endpoint'))
        if len(set(all_values)) != len(all_values) or settings.jwt_secret_key.get_secret_value() in all_values:
            raise ConfigurationError('Telemetry unavailable')
    return decoded


def validate_endpoint(settings, endpoint):
    if not endpoint:
        return
    target = urlsplit(endpoint)
    if (target.scheme not in {'http', 'https'} or not target.hostname
            or target.username is not None or target.password is not None
            or target.path != '/telemetry/events' or target.query or target.fragment
            or (settings.app_environment == 'production' and target.scheme != 'https')):
        raise ConfigurationError('Telemetry unavailable')


def region_settings(settings, jurisdiction):
    """Select keys only from server-resolved jurisdiction or a verified context."""
    keys(settings)
    if jurisdiction is None:
        return settings
    if jurisdiction not in {'US', 'UK'}:
        raise ContextError('Invalid telemetry context')
    if settings.telemetry_processing_region is not None:
        if jurisdiction != settings.telemetry_processing_region:
            raise ContextError('Invalid telemetry context')
        return settings  # Compatibility with previously configured single-region instances.
    region = jurisdiction.lower()
    update = {'telemetry_processing_region': jurisdiction,
              'telemetry_endpoint': getattr(settings, f'telemetry_{region}_endpoint')}
    for purpose in ('user', 'subject', 'clinic', 'context', 'resource'):
        update[f'telemetry_{purpose}_key'] = getattr(settings, f'telemetry_{region}_{purpose}_key')
    return settings.model_copy(update=update, deep=True)


def digest(key: str, purpose: str, identity: UUID):
    message = f'healthcore|{purpose}|v1|{str(identity).lower()}'.encode()
    return hmac.new(key.encode(), message, hashlib.sha256).hexdigest()


def user_id(settings, identity):
    return 'ps_' + digest(keys(settings)[0], 'telemetry-user', identity)


def subject_binding(settings, identity):
    return digest(keys(settings)[1], 'telemetry-subject', identity)


def clinic_binding(settings, identity):
    return digest(keys(settings)[2], 'telemetry-clinic', identity)


def decode_context(settings, token, actor):
    keys(settings)
    try:
        # This untrusted selector chooses a configured key only. All claims still
        # require signature verification and exact scope checks before use.
        header = jwt.get_unverified_header(token)
        selector = header.get('region', settings.telemetry_processing_region)
        if selector == 'GENERAL':
            selector = None
        if selector not in {'US', 'UK', None}:
            raise ContextError('Invalid telemetry context')
        if settings.telemetry_processing_region is None and 'region' not in header:
            raise ContextError('Invalid telemetry context')
        settings = region_settings(settings, selector)
        signing_key = keys(settings)[3]
        claims = jwt.decode(token, signing_key, algorithms=['HS256'], issuer=ISSUER, audience=AUDIENCE,
                            options={'require': ['exp', 'iat', 'iss', 'aud', 'sid', 'subjectBinding',
                                                 'environment', 'pseudonymVersion']})
        header = jwt.get_unverified_header(token)
        if (header.get('kid') != settings.telemetry_key_version
                or claims['pseudonymVersion'] != settings.telemetry_key_version
                or claims['processingRegion'] != settings.telemetry_processing_region
                or claims['environment'] != settings.app_environment
                or not hmac.compare_digest(claims['subjectBinding'], subject_binding(settings, actor.id))
                or str(UUID(claims['sid'])) != claims['sid']
                or claims['exp'] - claims['iat'] > settings.telemetry_context_ttl_seconds):
            raise ContextError('Invalid telemetry context')
        if 'jurisdiction' not in claims or 'clinicBinding' not in claims:
            raise ContextError('Invalid telemetry context')
        jurisdiction = claims['jurisdiction']
        if jurisdiction is not None and jurisdiction != settings.telemetry_processing_region:
            raise ContextError('Invalid telemetry context')
        if (jurisdiction is None) != (claims['clinicBinding'] is None):
            raise ContextError('Invalid telemetry context')
        return claims
    except (jwt.PyJWTError, ValueError, TypeError, KeyError) as error:
        raise ContextError('Invalid telemetry context') from error


def sign_context(settings, claims):
    return jwt.encode(claims, keys(settings)[3], algorithm='HS256', headers={'kid': settings.telemetry_key_version, 'region': settings.telemetry_processing_region or 'GENERAL'})


def now_seconds():
    return int(datetime.now(UTC).timestamp())
