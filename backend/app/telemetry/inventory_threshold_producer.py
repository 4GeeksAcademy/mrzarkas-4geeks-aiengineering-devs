"""Only persisted post-commit threshold crossings may become regional events."""
import asyncio
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.db import session as database
from app.inventory.models import InventoryMovement
from app.inventory.threshold_models import InventoryThresholdTransition
from app.inventory.policies import allow, scope
from app.reference_data.models import Clinic, Jurisdiction
from app.telemetry.identity import region_settings, user_id, clinic_binding
from app.telemetry.inventory_producer import resource_id
from app.telemetry.schemas import VERSION


async def resolve_transition(actor, transition_id):
    if database.SessionLocal is None:
        raise ValueError('Threshold source unavailable')
    async with database.SessionLocal() as session:
        transition = await session.get(InventoryThresholdTransition, transition_id)
        if transition is None or transition.kind not in {'activated', 'cleared'}:
            raise ValueError('Threshold source unavailable')
        movement = await session.get(InventoryMovement, transition.movement_id)
        if movement is None or movement.actor_id != actor.id or movement.result != 'accepted' or movement.kind not in {'in', 'out', 'adjust', 'correction'}:
            raise ValueError('Threshold source unavailable')
        allow(actor, 'adjust:write' if movement.kind in {'adjust', 'correction'} else 'movement:write')
        clinic = await session.get(Clinic, movement.clinic_id)
        if clinic is None:
            raise ValueError('Threshold scope unavailable')
        scope(actor, clinic)
        country = await session.get(Jurisdiction, clinic.jurisdiction_id)
        if (country is None or not country.is_active or country.key not in {'US', 'UK'}
                or transition.jurisdiction_id != country.id or transition.jurisdiction_key != country.key
                or movement.jurisdiction_id != country.id or movement.jurisdiction_key != country.key):
            raise ValueError('Threshold scope unavailable')
        return transition.kind, transition.episode_id, movement.item_id, clinic.id, country.key


async def _prepare(service, actor, transition_id, timestamp):
    try:
        kind, episode, item, clinic, region = await asyncio.wait_for(resolve_transition(actor, transition_id), timeout=.1)
        if service.closed:
            return
        settings = region_settings(service.settings, region)
        event = dict(eventId=str(uuid4()), timestamp=timestamp, sessionId=None, requestId=None,
            userId=user_id(settings, actor.id), schemaVersion=VERSION, event_type='inventory_threshold_' + kind,
            properties=dict(jurisdiction=region, environment=settings.app_environment,
                itemId=resource_id(settings, 'inventory_item', item),
                scopeId=resource_id(settings, 'inventory_scope', clinic),
                episodeId=resource_id(settings, 'inventory_episode', episode)))
        service.queue.enqueue(event, f'{region}:{clinic_binding(settings, clinic)}')
    except asyncio.CancelledError:
        service.discarded += 1
        raise
    except Exception:
        service.discarded += 1


def capture_threshold(actor, transition_id):
    try:
        from app.telemetry import incident_producer
        service = incident_producer._producer
        if service is None or transition_id is None:
            return False
        if service.closed or len(service.tasks) >= 16 or not isinstance(actor.id, UUID) or not isinstance(transition_id, UUID):
            service.discarded += 1
            return False
        task = asyncio.create_task(_prepare(service, actor, transition_id, datetime.now(UTC).isoformat()))
        service.tasks.add(task)
        task.add_done_callback(service._done)
        return True
    except Exception:
        return False
