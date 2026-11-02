"""Server-only capture of completed HTTP requests with authorized clinical scope."""
import asyncio
import math
from uuid import UUID, uuid4

from app.telemetry.context import resolve_clinic
from app.telemetry.identity import region_settings, user_id
from app.telemetry.schemas import VERSION

STATE_KEY = 'healthcore_telemetry_request'


def mark_request(request, actor, clinic_id):
    try:
        if request is not None and isinstance(actor.id, UUID) and isinstance(clinic_id, UUID):
            request.scope.setdefault('state', {})[STATE_KEY] = (actor, clinic_id)
    except Exception:
        pass


async def _prepare(service, actor, clinic_id, request_id, status, duration, timestamp):
    try:
        scope, region = await asyncio.wait_for(resolve_clinic(service.settings, actor, clinic_id=clinic_id), timeout=.1)
        if service.closed:
            return
        scoped = region_settings(service.settings, region)
        event = dict(eventId=str(uuid4()), timestamp=timestamp, sessionId=None,
                     userId=user_id(scoped, actor.id), event_type='api_request_completed',
                     schemaVersion=VERSION, requestId=str(request_id),
                     properties=dict(jurisdiction=region, environment=scoped.app_environment,
                                     route='incidents', statusCode=status, durationMs=duration))
        service.queue.enqueue(event, f'{region}:{scope}')
    except asyncio.CancelledError:
        service.discarded += 1
        raise
    except Exception:
        service.discarded += 1


def capture_request(actor, clinic_id, request_id, status, duration, timestamp):
    from app.telemetry import incident_producer
    service = incident_producer._producer
    if service is None:
        return False
    try:
        if service.closed or len(service.tasks) >= 16:
            raise ValueError('Producer unavailable')
        if any(not isinstance(value, UUID) for value in (actor.id, clinic_id, request_id)):
            raise ValueError('Invalid identifiers')
        if not isinstance(status, int) or not 100 <= status <= 599 or not math.isfinite(duration) or duration < 0:
            raise ValueError('Invalid measurement')
        task = asyncio.create_task(_prepare(service, actor, clinic_id, request_id, status, duration, timestamp))
        service.tasks.add(task)
        task.add_done_callback(service._done)
        return True
    except Exception:
        service.discarded += 1
        return False


GENERAL_STATE_KEY = 'healthcore_telemetry_general_request'
GENERAL_ROUTES = frozenset({'health', 'status'})


def mark_general_request(request, route):
    try:
        if request is not None and route in GENERAL_ROUTES:
            request.scope.setdefault('state', {})[GENERAL_STATE_KEY] = route
    except Exception:
        pass


def capture_general_request(route, request_id, status, duration, timestamp):
    from app.telemetry import incident_producer
    service = incident_producer._producer
    if service is None:
        return False
    try:
        if (service.closed or route not in GENERAL_ROUTES or not isinstance(request_id, UUID)
                or not isinstance(status, int) or not 100 <= status <= 599
                or not math.isfinite(duration) or duration < 0):
            service.discarded += 1
            return False
        event = dict(eventId=str(uuid4()), timestamp=timestamp, sessionId=None, userId=None,
            event_type='api_request_completed', schemaVersion=VERSION, requestId=str(request_id),
            properties=dict(jurisdiction=None, environment=service.settings.app_environment,
                route=route, statusCode=status, durationMs=duration))
        return service.queue.enqueue(event, 'GENERAL')
    except Exception:
        return False


AUTH_GENERAL_STATE_KEY = 'healthcore_telemetry_authenticated_general_request'


def mark_authenticated_general_request(request, actor, route):
    try:
        if request is not None and route == 'catalogs' and isinstance(actor.id, UUID):
            request.scope.setdefault('state', {})[AUTH_GENERAL_STATE_KEY] = (actor, route)
    except Exception:
        pass


def capture_authenticated_general_request(actor, route, request_id, status, duration, timestamp):
    from app.auth.roles import has_capability
    from app.telemetry import incident_producer
    service = incident_producer._producer
    if service is None:
        return False
    try:
        if (service.closed or route != 'catalogs' or not has_capability(actor.role, 'catalog:read')
                or service.settings.telemetry_processing_region is not None
                or any(not isinstance(value, UUID) for value in (actor.id, request_id))
                or not isinstance(status, int) or not 100 <= status <= 599
                or not math.isfinite(duration) or duration < 0):
            service.discarded += 1
            return False
        event = dict(eventId=str(uuid4()), timestamp=timestamp, sessionId=None,
            userId=user_id(service.settings, actor.id), event_type='api_request_completed',
            schemaVersion=VERSION, requestId=str(request_id),
            properties=dict(jurisdiction=None, environment=service.settings.app_environment,
                route='catalogs', statusCode=status, durationMs=duration))
        return service.queue.enqueue(event, 'GENERAL')
    except Exception:
        return False
