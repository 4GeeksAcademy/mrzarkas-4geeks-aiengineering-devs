"""Server-clock lifecycle, row-locked and isolated from business writes."""
from datetime import UTC, datetime, timedelta
from sqlalchemy import select, update, func
from fastapi import HTTPException
from app.db import session as database
from app.inventory.flow_models import InventoryTelemetryFlow as Flow
from app.reference_data.models import Clinic, Jurisdiction
from app.inventory.models import InventoryItem, InventoryClinicItem
from app.inventory.policies import allow, scope


def clock():
    return datetime.now(UTC)


def matches(row, actor, clinic_id, item_id, settings):
    return (row.actor_id == actor.id and row.clinic_id == clinic_id and row.item_id == item_id
            and row.jurisdiction_key == settings.telemetry_processing_region
            and row.environment == settings.app_environment and row.key_version == settings.telemetry_key_version)


async def record(actor, clinic_id, item_id, settings, flow_id, action, direction):
    if database.SessionLocal is None:
        return False
    allow(actor, 'stock:read' if action == 'product_selected' else 'movement:write')
    async with database.SessionLocal() as session, session.begin():
        clinic = await session.get(Clinic, clinic_id)
        item = await session.get(InventoryItem, item_id)
        country = await session.get(Jurisdiction, clinic.jurisdiction_id) if clinic else None
        if (clinic is None or item is None or not item.is_active or country is None
                or not country.is_active or country.key != settings.telemetry_processing_region):
            raise HTTPException(404, 'Inventory flow unavailable')
        scope(actor, clinic)
        if action != 'product_selected' and await session.get(InventoryClinicItem,(item_id,clinic_id)) is None:
            raise HTTPException(404, 'Inventory flow unavailable')
        row = await session.get(Flow, flow_id, with_for_update=True)
        current = clock()
        if row is None:
            if action not in {'product_selected','order_started'}:
                raise HTTPException(404, 'Inventory flow unavailable')
            row = Flow(flow_id=flow_id, actor_id=actor.id, clinic_id=clinic_id, item_id=item_id,
                jurisdiction_id=clinic.jurisdiction_id, jurisdiction_key=settings.telemetry_processing_region,
                environment=settings.app_environment, key_version=settings.telemetry_key_version,
                direction=direction, started_at=current, last_activity_at=current,
                last_step='selection' if action == 'product_selected' else 'validation', status='open')
            session.add(row)
        else:
            if not matches(row, actor, clinic_id, item_id, settings):
                raise HTTPException(403, 'Inventory flow unavailable')
            if row.status != 'open' or current-row.last_activity_at >= timedelta(minutes=30):
                raise HTTPException(409, 'Inventory flow closed')
            if direction is not None and row.direction not in {None,direction}:
                raise HTTPException(403, 'Inventory flow unavailable')
            if action in {'activity','confirmation'} and row.direction is None:
                raise HTTPException(409, 'Inventory flow not started')
            if action == 'order_started':
                row.direction = direction
            row.last_activity_at = current
            step = 'confirmation' if action == 'confirmation' else 'validation' if action in {'order_started','activity'} else 'selection'
            ranks = {'selection':0,'validation':1,'confirmation':2}
            if ranks[step] > ranks[row.last_step]: row.last_step = step
        await session.flush()
    return True


async def complete(session, movement, flow_id):
    try:
        if movement.kind not in {'in','out'}:
            return True
        async with session.begin_nested():
            rows = (await session.scalars(select(Flow).where(Flow.actor_id == movement.actor_id,
                Flow.item_id == movement.item_id, Flow.clinic_id == movement.clinic_id,
                Flow.status == 'open').order_by(Flow.flow_id).with_for_update())).all()
            current = clock()
            direction = 'inbound' if movement.kind == 'in' else 'outbound'
            for row in rows:
                # Only an exact authenticated business binding proves completion;
                # other outstanding flows become uncertain, never assumed abandoned.
                valid = (row.flow_id == flow_id and row.direction == direction
                         and row.jurisdiction_id == movement.jurisdiction_id
                         and row.jurisdiction_key == movement.jurisdiction_key)
                row.status = 'completed' if valid else 'uncertain'
                row.closed_at = current
            await session.flush()
        return True
    except Exception:
        # Persist a conservative disposition if ordinary tracking failed. This
        # second savepoint never rescues a failed outer business commit.
        try:
            async with session.begin_nested():
                await session.execute(update(Flow).where(Flow.actor_id == movement.actor_id,
                    Flow.item_id == movement.item_id, Flow.clinic_id == movement.clinic_id,
                    Flow.status == 'open').values(status='uncertain', closed_at=func.now()))
        except Exception:
            pass
        return False
