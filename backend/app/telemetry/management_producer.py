"""Capture confirmed clinic mutations using the persisted historical audit scope."""
import asyncio
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select

from app.auth.roles import has_capability
from app.db import session as database
from app.management.audit import ManagementAuditEvent
from app.reference_data.models import Jurisdiction
from app.telemetry.identity import clinic_binding, region_settings, user_id
from app.telemetry.incident_producer import resource_id
from app.telemetry.schemas import VERSION

ACTIONS = frozenset({'created', 'updated', 'activated', 'deactivated'})


async def resolve_audit(actor, audit_id):
    if not has_capability(actor.role, 'referenceData:manage') or database.SessionLocal is None:
        raise ValueError('Audit scope unavailable')
    async with database.SessionLocal() as session:
        audit = await session.get(ManagementAuditEvent, audit_id)
        if (audit is None or audit.actor_id != actor.id or audit.resource_type != 'clinics'
                or audit.action not in ACTIONS or not isinstance(audit.resource_id, UUID)):
            raise ValueError('Audit scope unavailable')
        snapshot = audit.after_data if audit.action == 'created' else audit.before_data
        if not isinstance(snapshot, dict) or not isinstance(snapshot.get('jurisdiction_id'), str):
            raise ValueError('Audit scope unavailable')
        jurisdiction_id = UUID(snapshot['jurisdiction_id'])
        # Historical classification does not reactivate or authorize an inactive clinic.
        region = await session.scalar(select(Jurisdiction.key).where(Jurisdiction.id == jurisdiction_id))
        if region not in {'US', 'UK'}:
            raise ValueError('Audit scope unavailable')
        return audit.resource_id, region, audit.action


async def _prepare(service, actor, audit_id, timestamp):
    try:
        clinic_id, region, action = await asyncio.wait_for(resolve_audit(actor, audit_id), timeout=.1)
        if service.closed:
            return
        scoped = region_settings(service.settings, region)
        event = dict(eventId=str(uuid4()), timestamp=timestamp, sessionId=None,
                     userId=user_id(scoped, actor.id), event_type='management_mutation_completed',
                     schemaVersion=VERSION, requestId=None,
                     properties=dict(jurisdiction=region, environment=scoped.app_environment,
                                     auditId=resource_id(scoped, 'audit', audit_id), resource='reference', action=action))
        service.queue.enqueue(event, f'{region}:{clinic_binding(scoped, clinic_id)}')
    except asyncio.CancelledError:
        service.discarded += 1
        raise
    except Exception:
        service.discarded += 1


def capture_management(actor, audit_id):
    from app.telemetry import incident_producer
    service = incident_producer._producer
    if service is None:
        return False
    try:
        if service.closed or len(service.tasks) >= 16 or not isinstance(actor.id, UUID) or not isinstance(audit_id, UUID):
            raise ValueError('Producer unavailable')
        task = asyncio.create_task(_prepare(service, actor, audit_id, datetime.now(UTC).isoformat()))
        service.tasks.add(task)
        task.add_done_callback(service._done)
        return True
    except Exception:
        service.discarded += 1
        return False
