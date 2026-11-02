"""Observe typed rejected attempts without retaining their input or error text."""
import asyncio
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.db import session as database
from app.inventory.policies import allow, scope
from app.inventory.models import InventoryItem
from app.reference_data.models import Clinic, Jurisdiction
from app.telemetry.identity import clinic_binding, region_settings, user_id
from app.telemetry.inventory_producer import resource_id
from app.telemetry.schemas import VERSION


async def resolve_attempt(actor, item_id, clinic_id, kind):
    if kind not in {'in', 'out', 'adjust', 'configuration'} or database.SessionLocal is None:
        raise ValueError('Inventory attempt unavailable')
    allow(actor, 'config:write' if kind == 'configuration' else
          'adjust:write' if kind == 'adjust' else 'movement:write')
    async with database.SessionLocal() as session:
        item = await session.get(InventoryItem, item_id)
        if item is None or not item.is_active:
            raise ValueError('Inventory item unavailable')
        clinic = await session.get(Clinic, clinic_id)
        if clinic is None:
            raise ValueError('Inventory scope unavailable')
        scope(actor, clinic)
        country = await session.get(Jurisdiction, clinic.jurisdiction_id)
        if country is None or not country.is_active or country.key not in {'US', 'UK'}:
            raise ValueError('Inventory scope unavailable')
        return country.key


async def _prepare(service, actor, item_id, clinic_id, kind, operation_id, timestamp):
    try:
        region = await asyncio.wait_for(resolve_attempt(actor, item_id, clinic_id, kind), timeout=.1)
        if service.closed:
            return
        scoped = region_settings(service.settings, region)
        event = dict(eventId=str(uuid4()), timestamp=timestamp, sessionId=None,
                     userId=user_id(scoped, actor.id), schemaVersion=VERSION, requestId=None,
                     event_type='stock_direct_update_rejected',
                     properties=dict(jurisdiction=region, environment=scoped.app_environment,
                                     operationId=resource_id(scoped, 'inventory_operation', operation_id),
                                     channel='api'))
        service.queue.enqueue(event, f'{region}:{clinic_binding(scoped, clinic_id)}')
    except asyncio.CancelledError:
        service.discarded += 1
        raise
    except Exception:
        service.discarded += 1


def capture_direct_stock(actor, item_id, clinic_id, kind, operation_id):
    try:
        from app.telemetry import incident_producer
        service = incident_producer._producer
        if service is None:
            return False
        if (service.closed or len(service.tasks) >= 16
                or kind not in {'in', 'out', 'adjust', 'configuration'}
                or any(not isinstance(value, UUID) for value in (actor.id, item_id, clinic_id, operation_id))):
            service.discarded += 1
            return False
        task = asyncio.create_task(_prepare(service, actor, item_id, clinic_id, kind, operation_id,
                                          datetime.now(UTC).isoformat()))
        service.tasks.add(task)
        task.add_done_callback(service._done)
        return True
    except Exception:
        return False
