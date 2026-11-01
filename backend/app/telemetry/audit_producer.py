"""Bounded capture of completed audit reads; no audit content leaves the API."""
import asyncio
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.telemetry.context import resolve_clinic
from app.telemetry.identity import region_settings, user_id
from app.telemetry.schemas import VERSION

STATE_KEY = 'healthcore_telemetry_audit_read'


def mark_audit(request, actor, clinic_id, surface):
    try:
        if request is not None and surface in {'incident', 'management'} and isinstance(clinic_id, UUID):
            request.scope.setdefault('state', {})[STATE_KEY] = (actor, clinic_id, surface)
    except Exception:
        pass  # Optional capture must not change the existing read response.


async def _prepare(service, actor, clinic_id, surface, timestamp):
    try:
        scope, region = await asyncio.wait_for(resolve_clinic(service.settings, actor, clinic_id=clinic_id), timeout=.1)
        if service.closed:
            return
        scoped = region_settings(service.settings, region)
        event = dict(eventId=str(uuid4()), timestamp=timestamp, sessionId=None,
                     userId=user_id(scoped, actor.id), event_type='audit_accessed',
                     schemaVersion=VERSION, requestId=None,
                     properties=dict(jurisdiction=region, environment=scoped.app_environment, surface=surface))
        service.queue.enqueue(event, f'{region}:{scope}')
    except asyncio.CancelledError:
        service.discarded += 1
        raise
    except Exception:
        service.discarded += 1


def capture_audit(actor, clinic_id, surface):
    from app.telemetry import incident_producer
    service = incident_producer._producer
    if service is None:
        return False
    try:
        if service.closed or len(service.tasks) >= 16 or surface not in {'incident', 'management'}:
            raise ValueError('Producer unavailable')
        if not isinstance(actor.id, UUID) or not isinstance(clinic_id, UUID):
            raise ValueError('Invalid identifiers')
        task = asyncio.create_task(_prepare(service, actor, clinic_id, surface, datetime.now(UTC).isoformat()))
        service.tasks.add(task)
        task.add_done_callback(service._done)
        return True
    except Exception:
        service.discarded += 1
        return False
