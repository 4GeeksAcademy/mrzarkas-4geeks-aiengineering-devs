from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from app.reference_data.models import Clinic, Jurisdiction
from .models import InventoryItem, InventoryClinicItem, InventoryLot, InventoryMovement, InventoryAudit
from .policies import allow, scope
from .schemas import ItemCreate, ItemRead, StockRead


async def flush(session):
    try:
        await session.flush()
    except IntegrityError as error:
        raise HTTPException(409, "Inventory reference or uniqueness conflict") from error


async def item(session, item_id, lock=False):
    query = select(InventoryItem).where(InventoryItem.id == item_id)
    if lock:
        query = query.with_for_update()
    value = await session.scalar(query)
    if value is None:
        raise HTTPException(404, "Inventory item not found")
    return value


def active(value):
    if not value.is_active:
        raise HTTPException(409, "Inventory item is inactive")


async def clinic(session, actor, clinic_id, lock=False):
    query = select(Clinic).where(Clinic.id == clinic_id)
    if lock:
        query = query.with_for_update()
    value = await session.scalar(query)
    if value is None:
        raise HTTPException(404, "Clinic not found")
    scope(actor, value)
    return value


async def config(session, item_id, clinic_id):
    value = await session.get(InventoryClinicItem, (item_id, clinic_id))
    if value is None:
        raise HTTPException(409, "Configure the mandatory clinic reorder point first")
    return value


async def lot(session, value, lot_id):
    if value.uses_lots != (lot_id is not None):
        raise HTTPException(422, "Lot requirement does not match the item")
    if lot_id is not None:
        found = await session.get(InventoryLot, lot_id)
        if found is None:
            raise HTTPException(404, "Lot not found")
        if found.item_id != value.id:
            raise HTTPException(422, "Lot does not belong to the item")


async def quantity(session, item_id, clinic_id=None, lot_id=None, filter_lot=False):
    query = select(func.coalesce(func.sum(InventoryMovement.delta), 0)).where(InventoryMovement.item_id == item_id)
    if clinic_id is not None:
        query = query.where(InventoryMovement.clinic_id == clinic_id)
    if filter_lot:
        query = query.where(InventoryMovement.lot_id == lot_id)
    return int(await session.scalar(query))


def audit(session, actor, value, action, before=None, after=None, clinic_id=None, reason=None, country=None):
    session.add(InventoryAudit(item_id=value.id, clinic_id=clinic_id, actor_id=actor.id,
        action=action, before_data=before, after_data=after, reason=reason,
        jurisdiction_id=country.id if country else None, jurisdiction_key=country.key if country else None, result="accepted"))


def snapshot(value):
    return ItemRead.model_validate(value).model_dump(mode="json")


async def create_item(session, actor, payload):
    allow(actor, "catalog:manage")
    value = InventoryItem(**payload.model_dump(), created_by=actor.id)
    session.add(value)
    await flush(session)
    audit(session, actor, value, "item_created", after=snapshot(value))
    await flush(session)
    return value


async def update_item(session, actor, item_id, payload):
    allow(actor, "catalog:manage")
    value = await item(session, item_id, True)
    active(value)
    before = snapshot(value)
    merged_data = {**{k: getattr(value, k) for k in ItemCreate.model_fields}, **payload.model_dump(exclude_unset=True)}
    from pydantic import ValidationError
    try:
        merged = ItemCreate.model_validate(merged_data)
    except ValidationError as error:
        raise HTTPException(422, "Invalid item presentation") from error
    for key in payload.model_fields_set:
        setattr(value, key, getattr(merged, key))
    audit(session, actor, value, "item_updated", before, snapshot(value))
    await flush(session)
    return value


async def deactivate(session, actor, item_id, reason):
    allow(actor, "catalog:manage")
    value = await item(session, item_id, True)
    active(value)
    if await quantity(session, item_id) != 0:
        raise HTTPException(409, "Cannot deactivate an item with remaining stock")
    before = snapshot(value)
    value.is_active = False
    audit(session, actor, value, "item_deactivated", before, snapshot(value), reason=reason)
    await flush(session)
    return value


async def configure(session, actor, item_id, clinic_id, payload):
    allow(actor, "config:write")
    clinic_value = await clinic(session, actor, clinic_id, True)
    country = await session.get(Jurisdiction, clinic_value.jurisdiction_id)
    value = await item(session, item_id, True)
    active(value)
    current = await session.get(InventoryClinicItem, (item_id, clinic_id))
    before = {"reorder_point": current.reorder_point} if current else None
    if current:
        current.reorder_point = payload.reorder_point
    else:
        current = InventoryClinicItem(item_id=item_id, clinic_id=clinic_id, reorder_point=payload.reorder_point)
        session.add(current)
    audit(session, actor, value, "reorder_configured", before, payload.model_dump(), clinic_id, country=country)
    await flush(session)
    return current


async def create_lot(session, actor, item_id, payload):
    allow(actor, "catalog:manage")
    value = await item(session, item_id, True)
    active(value)
    if not value.uses_lots:
        raise HTTPException(422, "Item does not use lots")
    created = InventoryLot(item_id=item_id, code=payload.code)
    session.add(created)
    await flush(session)
    audit(session, actor, value, "lot_created", after={"lot_id": str(created.id), "code": created.code})
    await flush(session)
    return created


async def movement(session, actor, payload):
    allow(actor, "adjust:write" if payload.kind == "adjust" else "movement:write")
    clinic_value = await clinic(session, actor, payload.clinic_id, True)
    country = await session.get(Jurisdiction, clinic_value.jurisdiction_id)
    value = await item(session, payload.item_id, True)
    active(value)
    await config(session, value.id, payload.clinic_id)
    await lot(session, value, payload.lot_id)
    previous = await quantity(session, value.id, payload.clinic_id, payload.lot_id, value.uses_lots)
    if payload.kind == "adjust":
        delta = payload.counted_quantity - previous
    else:
        factor = value.pack_size if payload.unit == "pack" else 1
        if payload.unit == "pack" and value.pack_label is None:
            raise HTTPException(422, "Item has no pack presentation")
        delta = payload.quantity * factor * (1 if payload.kind == "in" else -1)
    if previous + delta < 0:
        raise HTTPException(409, "Insufficient stock")
    created = InventoryMovement(item_id=value.id, clinic_id=payload.clinic_id, lot_id=payload.lot_id,
        kind=payload.kind, delta=delta, previous_quantity=previous, counted_quantity=payload.counted_quantity,
        unit=value.unit, pack_size=value.pack_size, pack_label=value.pack_label, reason=payload.reason,
        actor_id=actor.id, jurisdiction_id=country.id, jurisdiction_key=country.key, result="accepted")
    session.add(created)
    await flush(session)
    return created


async def correct(session, actor, movement_id, reason):
    allow(actor, "adjust:write")
    original = await session.get(InventoryMovement, movement_id)
    if original is None:
        raise HTTPException(404, "Movement not found")
    clinic_value = await clinic(session, actor, original.clinic_id, True)
    country = await session.get(Jurisdiction, clinic_value.jurisdiction_id)
    value = await item(session, original.item_id, True)
    active(value)
    if original.kind == "correction" or await session.scalar(select(InventoryMovement.id).where(InventoryMovement.correction_of == original.id)):
        raise HTTPException(409, "Movement cannot be compensated again")
    previous = await quantity(session, value.id, original.clinic_id, original.lot_id, value.uses_lots)
    if previous - original.delta < 0:
        raise HTTPException(409, "Compensation would leave negative stock")
    created = InventoryMovement(item_id=value.id, clinic_id=original.clinic_id, lot_id=original.lot_id,
        kind="correction", delta=-original.delta, previous_quantity=previous, counted_quantity=None,
        correction_of=original.id, unit=original.unit, pack_size=original.pack_size,
        pack_label=original.pack_label, reason=reason, actor_id=actor.id,
        jurisdiction_id=country.id, jurisdiction_key=country.key, result="accepted")
    session.add(created)
    await flush(session)
    return created


async def stock(session, actor, item_id, clinic_id, lot_id=None):
    allow(actor, "stock:read")
    await clinic(session, actor, clinic_id)
    value = await item(session, item_id)
    threshold = await config(session, item_id, clinic_id)
    if lot_id is not None:
        await lot(session, value, lot_id)
    # A single SELECT snapshot returns lot quantity AND clinic total for reorder.
    conditions = [InventoryMovement.item_id == item_id, InventoryMovement.clinic_id == clinic_id]
    from sqlalchemy import case
    lot_sum = func.coalesce(func.sum(case((InventoryMovement.lot_id == lot_id, InventoryMovement.delta), else_=0)), 0)
    total_sum = func.coalesce(func.sum(InventoryMovement.delta), 0)
    total, lot_quantity = (await session.execute(select(total_sum, lot_sum).where(*conditions))).one()
    amount = int(lot_quantity if lot_id else total)
    return StockRead(item_id=item_id, clinic_id=clinic_id, lot_id=lot_id, quantity=amount,
        unit=value.unit, pack_label=value.pack_label, pack_size=value.pack_size,
        complete_packs=amount // value.pack_size, remaining_units=amount % value.pack_size,
        reorder_point=threshold.reorder_point, below_reorder=int(total) < threshold.reorder_point)


async def history_clinic(session, actor, clinic_id):
    """Authorize historical scope without reclassifying events after a country change."""
    from .policies import INVENTORY_REGIONAL, INVENTORY_AUDITOR
    value = await session.get(Clinic, clinic_id)
    if value is None:
        raise HTTPException(404, "Clinic not found")
    if actor.role not in {INVENTORY_REGIONAL, INVENTORY_AUDITOR}:
        scope(actor, value)
        return value
    accepted = value.jurisdiction_id in actor.jurisdiction_ids
    if not accepted:
        for model in (InventoryMovement, InventoryAudit):
            if await session.scalar(select(model.id).where(model.clinic_id == clinic_id,
                model.jurisdiction_id.in_(actor.jurisdiction_ids)).limit(1)):
                accepted = True
                break
    if not accepted:
        raise HTTPException(403, "Clinic outside inventory scope")
    return value
