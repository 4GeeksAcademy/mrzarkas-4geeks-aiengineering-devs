"""Capture comparable clinic-scoped inventory audit reads without their content."""
import asyncio
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.db import session as database
from app.inventory.policies import allow, scope
from app.reference_data.models import Clinic, Jurisdiction
from app.telemetry.identity import clinic_binding, region_settings, user_id
from app.telemetry.schemas import VERSION

STATE_KEY = 'healthcore_telemetry_inventory_audit'


def mark_inventory_audit(request, actor, clinic_id, countries):
    try:
        if request is not None and isinstance(clinic_id, UUID) and len(countries) <= 100:
            request.scope.setdefault('state', {})[STATE_KEY] = (actor, clinic_id, frozenset(countries))
    except Exception:
        pass


async def resolve_audit(actor, clinic_id, countries):
    if database.SessionLocal is None:
        raise ValueError('Inventory view unavailable')
    allow(actor, 'audit:read')
    async with database.SessionLocal() as session:
        clinic = await session.get(Clinic, clinic_id)
        if clinic is None:
            raise ValueError('Inventory scope unavailable')
        scope(actor, clinic)
        country = await session.get(Jurisdiction, clinic.jurisdiction_id)
        if country is None or not country.is_active or country.key not in {'US', 'UK'}:
            raise ValueError('Inventory scope unavailable')
        if any(identity != country.id for identity in countries):
            raise ValueError('Non-comparable audit history')
        return country.key


async def _prepare(service, actor, clinic_id, countries, timestamp):
    try:
        region = await asyncio.wait_for(resolve_audit(actor, clinic_id, countries), timeout=.1)
        if service.closed:
            return
        scoped = region_settings(service.settings, region)
        event = dict(eventId=str(uuid4()), timestamp=timestamp, sessionId=None,
                     userId=user_id(scoped, actor.id), schemaVersion=VERSION, requestId=None,
                     event_type='audit_accessed', properties=dict(jurisdiction=region,
                     environment=scoped.app_environment, surface='inventory'))
        service.queue.enqueue(event, f'{region}:{clinic_binding(scoped, clinic_id)}')
    except asyncio.CancelledError:
        service.discarded += 1
        raise
    except Exception:
        service.discarded += 1


def capture_inventory_audit(actor, clinic_id, countries):
    try:
        from app.telemetry import incident_producer
        service = incident_producer._producer
        if service is None:
            return False
        if (service.closed or len(service.tasks) >= 16 or len(countries) > 100
                or any(not isinstance(value, UUID) for value in (actor.id, clinic_id))):
            service.discarded += 1
            return False
        task = asyncio.create_task(_prepare(service, actor, clinic_id, countries, datetime.now(UTC).isoformat()))
        service.tasks.add(task)
        task.add_done_callback(service._done)
        return True
    except Exception:
        return False
