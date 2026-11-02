"""Server-validated UI gesture ingress, not a confirmed inventory mutation."""
from datetime import UTC, datetime
from uuid import uuid4

from app.telemetry.identity import user_id, clinic_binding
from app.telemetry.schemas import VERSION


def capture_flow(service, settings, actor, clinic_id, action, flow_id, direction):
    try:
        properties = dict(jurisdiction=settings.telemetry_processing_region,
            environment=settings.app_environment, flowId=flow_id)
        if action == 'order_started':
            properties['direction'] = direction
        event = dict(eventId=str(uuid4()), timestamp=datetime.now(UTC).isoformat(),
            userId=user_id(settings, actor.id), sessionId=None, requestId=None,
            schemaVersion=VERSION, event_type=action, properties=properties)
        return service.queue.enqueue(event, f'{settings.telemetry_processing_region}:{clinic_binding(settings, clinic_id)}')
    except Exception:
        return False
