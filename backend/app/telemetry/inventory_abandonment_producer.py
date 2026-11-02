"""Bounded durable closure; delivery after commit remains best effort."""
import asyncio
from datetime import timedelta
from uuid import uuid4
from sqlalchemy import select
from app.db import session as database
from app.inventory.flow_models import InventoryTelemetryFlow as Flow
from app.inventory.flow_lifecycle import clock
from app.inventory.models import InventoryItem
from app.reference_data.models import Clinic, Jurisdiction
from app.telemetry.identity import region_settings, user_id, clinic_binding
from app.telemetry.schemas import VERSION


async def sweep(service):
    if service is None or service.closed or database.SessionLocal is None:
        return 0
    events = []
    async with database.SessionLocal() as session, session.begin():
        current = clock()
        uncertain = getattr(service, 'inventory_flow_uncertain', False)
        query = select(Flow).where(Flow.status == 'open')
        if not uncertain:
            query = query.where(Flow.last_activity_at <= current-timedelta(minutes=30))
        rows = (await session.scalars(query.order_by(Flow.last_activity_at, Flow.flow_id)
            .limit(100).with_for_update(skip_locked=True))).all()
        for row in rows:
            try:
                clinic = await session.get(Clinic, row.clinic_id)
                country = await session.get(Jurisdiction, row.jurisdiction_id)
                item = await session.get(InventoryItem, row.item_id)
                scoped = region_settings(service.settings, row.jurisdiction_key)
                valid = (clinic is not None and clinic.is_active and clinic.jurisdiction_id == row.jurisdiction_id
                    and country is not None and country.is_active and country.key == row.jurisdiction_key
                    and item is not None and item.is_active and row.environment == scoped.app_environment
                    and row.key_version == scoped.telemetry_key_version
                    and not uncertain)
                if not valid: raise ValueError('Uncertain flow context')
                properties = dict(jurisdiction=row.jurisdiction_key, environment=row.environment,
                    flowId=row.flow_id, lastStep=row.last_step,
                    durationMs=max(0, (current-row.started_at).total_seconds()*1000))
                event = dict(eventId=str(uuid4()), timestamp=current.isoformat(), schemaVersion=VERSION,
                    sessionId=None, requestId=None, userId=user_id(scoped,row.actor_id),
                    event_type='order_abandoned', properties=properties)
                events.append((event, f'{row.jurisdiction_key}:{clinic_binding(scoped,row.clinic_id)}'))
                row.status = 'abandoned'
            except Exception:
                row.status = 'uncertain'
            row.closed_at = current
        await session.flush()
    if uncertain and not rows:
        service.inventory_flow_uncertain = False
    for event, binding in events:
        try:
            if not service.closed: service.queue.enqueue(event, binding)
        except Exception:
            pass
    return len(events)


async def run(service):
    try:
        while not service.closed:
            try:
                await asyncio.wait_for(sweep(service), timeout=1)
            except Exception:
                service.discarded += 1
            await asyncio.sleep(60)
    except asyncio.CancelledError:
        raise


def start(service):
    return asyncio.create_task(run(service)) if service is not None else None


async def stop(task):
    if task is not None:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
