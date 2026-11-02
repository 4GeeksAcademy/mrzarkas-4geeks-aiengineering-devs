"""Best-effort capture of committed inventory movements, with scoped regional identity."""
import asyncio
import hashlib
import hmac
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.db import session as database
from app.inventory.models import InventoryMovement
from app.inventory.policies import allow, scope
from app.reference_data.models import Clinic, Jurisdiction
from app.telemetry.identity import clinic_binding, region_settings, user_id
from app.telemetry.incident_producer import resource_key
from app.telemetry.schemas import VERSION

EVENTS = {'in': 'inbound_order_completed', 'out': 'outbound_order_completed',
          'adjust': 'inventory_adjustment_completed'}


def resource_id(settings, purpose, identity):
    if purpose not in {'inventory_operation', 'inventory_movement', 'inventory_item', 'inventory_flow', 'inventory_episode', 'inventory_scope', 'inventory_check'} or not isinstance(identity, UUID):
        raise ValueError('Invalid inventory resource')
    version = settings.telemetry_key_version
    subkey = hmac.new(resource_key(settings), f'healthcore|resource-key|{purpose}|{version}'.encode(), hashlib.sha256).digest()
    message = f'healthcore|telemetry-resource|{purpose}|{version}|{identity}'.encode()
    return 'ps_' + hmac.new(subkey, message, hashlib.sha256).hexdigest()


async def resolve_movement(actor, movement_id):
    if database.SessionLocal is None:
        raise ValueError('Inventory source unavailable')
    async with database.SessionLocal() as session:
        movement = await session.get(InventoryMovement, movement_id)
        if (movement is None or movement.actor_id != actor.id or movement.kind not in EVENTS
                or movement.result != 'accepted'):
            raise ValueError('Inventory source unavailable')
        allow(actor, 'adjust:write' if movement.kind == 'adjust' else 'movement:write')
        clinic = await session.get(Clinic, movement.clinic_id)
        if clinic is None:
            raise ValueError('Inventory scope unavailable')
        scope(actor, clinic)
        country = await session.get(Jurisdiction, clinic.jurisdiction_id)
        if (country is None or not country.is_active or country.key not in {'US', 'UK'}
                or movement.jurisdiction_id != country.id or movement.jurisdiction_key != country.key):
            raise ValueError('Inventory scope unavailable')
        if any(not isinstance(value, UUID) for value in (movement.id, movement.item_id, clinic.id)):
            raise ValueError('Inventory source unavailable')
        return movement.id, movement.item_id, clinic.id, country.key, movement.kind


async def _prepare(service, actor, movement_id, timestamp):
    try:
        identity, item_id, clinic_id, region, kind = await asyncio.wait_for(resolve_movement(actor, movement_id), timeout=.1)
        if service.closed:
            return
        scoped = region_settings(service.settings, region)
        properties = dict(jurisdiction=region, environment=scoped.app_environment,
                          operationId=resource_id(scoped, 'inventory_operation', identity),
                          movementId=resource_id(scoped, 'inventory_movement', identity))
        if kind != 'adjust':
            properties['itemId'] = resource_id(scoped, 'inventory_item', item_id)
        event = dict(eventId=str(uuid4()), timestamp=timestamp, sessionId=None,
                     userId=user_id(scoped, actor.id), event_type=EVENTS[kind],
                     schemaVersion=VERSION, requestId=None, properties=properties)
        service.queue.enqueue(event, f'{region}:{clinic_binding(scoped, clinic_id)}')
    except asyncio.CancelledError:
        service.discarded += 1
        raise
    except Exception:
        service.discarded += 1


def capture_inventory(actor, movement_id):
    try:
        from app.telemetry import incident_producer
        service = incident_producer._producer
        if service is None:
            return False
        if service.closed or len(service.tasks) >= 16 or not isinstance(actor.id, UUID) or not isinstance(movement_id, UUID):
            service.discarded += 1
            return False
        task = asyncio.create_task(_prepare(service, actor, movement_id, datetime.now(UTC).isoformat()))
        service.tasks.add(task)
        task.add_done_callback(service._done)
        return True
    except Exception:
        return False  # Optional capture never changes a confirmed business operation.
