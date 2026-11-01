"""General security facts with bounded, server-only credential deduplication."""
import hashlib
import hmac
import time
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.telemetry.identity import keys, user_id
from app.telemetry.schemas import VERSION

STATE_KEY = 'healthcore_telemetry_security'
OPERATIONS = {
    'incident:create': 'create', 'incident:list': 'read', 'incident:read': 'read',
    'incident:update': 'update', 'incident:updateOwnArea': 'update', 'incident:changeSeverity': 'update',
    'incident:transition': 'transition', 'incident:close': 'transition', 'incident:reopen': 'transition',
    'incident:assign': 'assign', 'catalog:read': 'read', 'catalog:manage': 'manage',
    'referenceData:read': 'read', 'referenceData:manage': 'manage', 'audit:read': 'read',
    'complianceReview:read': 'read', 'complianceReview:manage': 'manage',
}


def _state(request):
    if request is None or request.scope.get('path', '').rstrip('/') in {'/telemetry/context', '/telemetry/events'}:
        return None
    return request.scope.setdefault('state', {}).setdefault(STATE_KEY, {})


def mark_success(request, actor, token, expiry):
    try:
        from app.telemetry import incident_producer
        service = incident_producer._producer
        if service is None or service.closed or not isinstance(expiry, int) or isinstance(expiry, bool) or expiry <= time.time():
            return
        state = _state(request)
        if state is None:
            return
        secret = keys(service.settings)[3].encode()
        derived = hmac.new(secret, b'healthcore|credential-dedup|v1', hashlib.sha256).digest()
        digest = hmac.new(derived, token.encode(), hashlib.sha256).hexdigest()
        state['success'] = (actor, digest, expiry)
    except Exception:
        pass


def mark_failure(request, reason):
    try:
        state = _state(request)
        if state is not None and reason in {'missing', 'invalid', 'expired'}:
            state['failure'] = reason
    except Exception:
        pass


def mark_denial(request, actor, capability):
    try:
        state = _state(request)
        if state is not None and capability in OPERATIONS:
            state['denial'] = (actor, OPERATIONS[capability])
    except Exception:
        pass


def capture_security(descriptor, status, request_id):
    from app.telemetry import incident_producer
    service = incident_producer._producer
    if service is None:
        return
    try:
        if service.closed or not isinstance(request_id, UUID):
            return
        config = service.settings
        keys(config)
        now = time.time()
        expired = [digest for digest, expiry in service.security_seen.items() if expiry <= now]
        for digest in expired:
            del service.security_seen[digest]
        timestamp = datetime.now(UTC).isoformat()

        def enqueue(name, actor=None, **properties):
            event = dict(eventId=str(uuid4()), timestamp=timestamp, sessionId=None,
                         userId=user_id(config, actor.id) if actor is not None else None,
                         event_type=name, schemaVersion=VERSION, requestId=str(request_id),
                         properties=dict(jurisdiction=None, environment=config.app_environment, **properties))
            return service.queue.enqueue(event, 'GENERAL:security')

        success = descriptor.get('success')
        if success is not None:
            actor, digest, expiry = success
            if expiry > now and digest not in service.security_seen:
                if len(service.security_seen) < 1024:
                    if enqueue('authentication_succeeded', actor, channel='api'):
                        service.security_seen[digest] = expiry
                else:
                    service.discarded += 1
        if status == 401 and descriptor.get('failure') in {'missing', 'invalid', 'expired'}:
            enqueue('authentication_failed', reasonCode=descriptor['failure'])
        if status == 403 and descriptor.get('denial') is not None:
            actor, operation = descriptor['denial']
            enqueue('authorization_denied', actor, reasonCode='capability', operation=operation)
    except Exception:
        service.discarded += 1
