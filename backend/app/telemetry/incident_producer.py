"""Capture only confirmed incident facts; never read within the business transaction."""
import asyncio
import hashlib
import hmac
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.core.config import get_settings
from app.telemetry.context import resolve_clinic
from app.telemetry.identity import ConfigurationError, keys, user_id, region_settings
from app.telemetry.schemas import VERSION
from app.telemetry.server import INCIDENT_EVENTS, ServerQueue


def resource_key(settings):
    existing = keys(settings)
    secret = settings.telemetry_resource_key
    if secret is None:
        raise ConfigurationError('Resource producer unavailable')
    value = secret.get_secret_value()
    if len(value.encode()) < 32 or value in existing or value == settings.jwt_secret_key.get_secret_value():
        raise ConfigurationError('Resource producer unavailable')
    return value.encode()


def resource_id(settings, purpose, identity):
    if purpose not in {'incident', 'audit'} or not isinstance(identity, UUID):
        raise ValueError('Invalid resource purpose')
    # Separate derived subkeys and messages for incident and audit identifiers.
    version = settings.telemetry_key_version
    subkey = hmac.new(resource_key(settings), f'healthcore|resource-key|{purpose}|{version}'.encode(), hashlib.sha256).digest()
    message = f'healthcore|telemetry-resource|{purpose}|{version}|{identity}'.encode()
    return 'ps_' + hmac.new(subkey, message, hashlib.sha256).hexdigest()


class IncidentProducer:
    def __init__(self, settings, *, queue=None):
        if settings.telemetry_processing_region is None:
            for region in ('US', 'UK'):
                resource_key(region_settings(settings, region))
        else:
            resource_key(settings)
        self.settings = settings.model_copy(deep=True)
        self.queue = queue or ServerQueue()
        self.tasks = set()
        self.closed = False
        self.discarded = 0
        self.security_seen = {}
        self.cache_sampler = None
        from app.telemetry.diagnostic_producer import DiagnosticChannel
        self.diagnostic_channel = DiagnosticChannel(self.settings)
        self.queue.diagnostic_callback = self.diagnostic_channel.capture

    def capture(self, event_type, actor, clinic_id, incident_id, audit_id):
        try:
            if self.closed or event_type not in INCIDENT_EVENTS or len(self.tasks) >= 16:
                raise ValueError('Producer unavailable')
            if any(not isinstance(identity, UUID) for identity in [actor.id, clinic_id, incident_id, audit_id]):
                raise ValueError('Invalid identifiers')
            timestamp = datetime.now(UTC).isoformat()
            task = asyncio.create_task(self._prepare(event_type, actor, clinic_id, incident_id, audit_id, timestamp))
            self.tasks.add(task)
            task.add_done_callback(self._done)
            return True
        except Exception:
            self.discarded += 1
            return False

    def _done(self, task):
        self.tasks.discard(task)
        if not task.cancelled():
            task.exception()

    async def _prepare(self, event_type, actor, clinic_id, incident_id, audit_id, timestamp):
        try:
            scope, jurisdiction = await asyncio.wait_for(resolve_clinic(self.settings, actor, clinic_id=clinic_id), timeout=.1)
            if self.closed:
                return
            scoped = region_settings(self.settings, jurisdiction)
            event = dict(eventId=str(uuid4()), timestamp=timestamp, sessionId=None,
                         userId=user_id(scoped, actor.id), event_type=event_type,
                         schemaVersion=VERSION, requestId=None,
                         properties=dict(jurisdiction=jurisdiction, environment=self.settings.app_environment,
                                         incidentId=resource_id(scoped, 'incident', incident_id),
                                         auditId=resource_id(scoped, 'audit', audit_id)))
            self.queue.enqueue(event, f'{jurisdiction}:{scope}')
        except asyncio.CancelledError:
            self.discarded += 1
            raise
        except Exception:
            self.discarded += 1

    async def close(self):
        self.closed = True
        if self.cache_sampler is not None:
            await self.cache_sampler.close()
            self.cache_sampler = None
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks.clear()
        self.security_seen.clear()
        await self.queue.close()
        await self.diagnostic_channel.close()


_producer = None


def start():
    global _producer
    if _producer is not None and not _producer.closed:
        return _producer
    try:
        _producer = IncidentProducer(get_settings())
        try:
            from app.catalogs.cache import catalog_cache
            from app.telemetry.health_cache_producer import CacheSampler
            _producer.cache_sampler = CacheSampler(_producer, catalog_cache).start()
        except Exception:
            _producer.discarded += 1
    except Exception:
        _producer = None  # Optional producer must never prevent API startup.
    return _producer


async def stop():
    global _producer
    producer, _producer = _producer, None
    if producer is not None:
        await producer.close()


def capture_incident(event_type, actor, clinic_id, incident_id, audit_id):
    try:
        if _producer is not None:
            _producer.capture(event_type, actor, clinic_id, incident_id, audit_id)
    except Exception:
        pass  # No optional telemetry failure may change a confirmed mutation.
