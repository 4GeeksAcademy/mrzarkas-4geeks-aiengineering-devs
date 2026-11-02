"""Capture completed explicitly clinic-scoped reads without exporting their rows."""
import asyncio
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.db import session as database
from app.inventory.policies import allow, scope
from app.reference_data.models import Clinic, Jurisdiction
from app.telemetry.identity import clinic_binding, region_settings, user_id
from app.telemetry.schemas import VERSION

STATE_KEY = 'healthcore_telemetry_inventory_view'
VIEWS = frozenset({'stock', 'reorder', 'movements'})


def mark_view(request, actor, clinic_id, view):
    try:
        if request is not None and isinstance(clinic_id, UUID) and view in VIEWS:
            request.scope.setdefault('state', {})[STATE_KEY] = (actor, clinic_id, view)
    except Exception:
        pass


async def resolve_view(actor, clinic_id, view):
    if view not in VIEWS or database.SessionLocal is None:
        raise ValueError('Inventory view unavailable')
    allow(actor, 'history:read' if view == 'movements' else 'stock:read')
    async with database.SessionLocal() as session:
        clinic = await session.get(Clinic, clinic_id)
        if clinic is None:
            raise ValueError('Inventory scope unavailable')
        scope(actor, clinic)
        country = await session.get(Jurisdiction, clinic.jurisdiction_id)
        if country is None or not country.is_active or country.key not in {'US', 'UK'}:
            raise ValueError('Inventory scope unavailable')
        return country.key


async def _prepare(service, actor, clinic_id, view, timestamp):
    try:
        region = await asyncio.wait_for(resolve_view(actor, clinic_id, view), timeout=.1)
        if service.closed:
            return
        scoped = region_settings(service.settings, region)
        event = dict(eventId=str(uuid4()), timestamp=timestamp, sessionId=None,
                     userId=user_id(scoped, actor.id), schemaVersion=VERSION, requestId=None,
                     event_type='inventory_viewed', properties=dict(jurisdiction=region,
                     environment=scoped.app_environment, view=view))
        service.queue.enqueue(event, f'{region}:{clinic_binding(scoped, clinic_id)}')
    except asyncio.CancelledError:
        service.discarded += 1
        raise
    except Exception:
        service.discarded += 1


def capture_view(actor, clinic_id, view):
    try:
        from app.telemetry import incident_producer
        service = incident_producer._producer
        if service is None:
            return False
        if (service.closed or len(service.tasks) >= 16 or view not in VIEWS
                or any(not isinstance(value, UUID) for value in (actor.id, clinic_id))):
            service.discarded += 1
            return False
        task = asyncio.create_task(_prepare(service, actor, clinic_id, view, datetime.now(UTC).isoformat()))
        service.tasks.add(task)
        task.add_done_callback(service._done)
        return True
    except Exception:
        return False
