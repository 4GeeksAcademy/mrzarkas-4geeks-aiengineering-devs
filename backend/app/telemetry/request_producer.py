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
