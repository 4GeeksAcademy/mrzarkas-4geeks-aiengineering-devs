from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import Actor, get_current_actor
from app.db.session import get_session
from app.error_contracts import error_responses
from app.reference_data.models import Clinic
from . import service as svc
from .access_audit import InventoryRoute, inventory_actor, inventory_session
from .models import InventoryItem, InventoryClinicItem, InventoryLot, InventoryMovement, InventoryAudit, InventoryAccessDenial
from .policies import allow, INVENTORY_OPERATOR, INVENTORY_MANAGER, INVENTORY_REGIONAL, INVENTORY_AUDITOR
from .schemas import (ItemCreate, ItemUpdate, ItemRead, ReasonRequest, ClinicConfig,
    ClinicConfigRead, LotCreate, LotRead, MovementCreate, MovementRead, StockRead, AuditRead, AccessDenialRead)

router = APIRouter(prefix="/inventory", tags=["inventory"], route_class=InventoryRoute, responses=error_responses(401, 403, 404, 409, 422, 503))
ActorDep = Depends(inventory_actor)
SessionDep = Depends(inventory_session)


@router.post("/items", response_model=ItemRead, status_code=201)
async def create_item(payload: ItemCreate, actor: Actor = ActorDep, session: AsyncSession = SessionDep):
    async with session.begin():
        return await svc.create_item(session, actor, payload)


@router.get("/items", response_model=list[ItemRead])
async def list_items(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100), actor: Actor = ActorDep, session: AsyncSession = SessionDep):
    allow(actor, "catalog:read")
    return (await session.scalars(select(InventoryItem).order_by(InventoryItem.product_code, InventoryItem.id).offset(offset).limit(limit))).all()


@router.get("/items/{item_id}", response_model=ItemRead)
async def read_item(item_id: UUID, actor: Actor = ActorDep, session: AsyncSession = SessionDep):
    allow(actor, "catalog:read")
    return await svc.item(session, item_id)


@router.patch("/items/{item_id}", response_model=ItemRead)
async def update_item(item_id: UUID, payload: ItemUpdate, actor: Actor = ActorDep, session: AsyncSession = SessionDep):
    async with session.begin():
        return await svc.update_item(session, actor, item_id, payload)


@router.post("/items/{item_id}/deactivation", response_model=ItemRead)
async def deactivate(item_id: UUID, payload: ReasonRequest, actor: Actor = ActorDep, session: AsyncSession = SessionDep):
    async with session.begin():
        return await svc.deactivate(session, actor, item_id, payload.reason)


@router.post("/items/{item_id}/clinics/{clinic_id}/configuration", response_model=ClinicConfigRead)
async def configure(item_id: UUID, clinic_id: UUID, payload: ClinicConfig, actor: Actor = ActorDep, session: AsyncSession = SessionDep):
    async with session.begin():
        return await svc.configure(session, actor, item_id, clinic_id, payload)


@router.post("/items/{item_id}/lots", response_model=LotRead, status_code=201)
async def create_lot(item_id: UUID, payload: LotCreate, actor: Actor = ActorDep, session: AsyncSession = SessionDep):
    async with session.begin():
        return await svc.create_lot(session, actor, item_id, payload)


@router.get("/items/{item_id}/lots", response_model=list[LotRead])
async def lots(item_id: UUID, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100), actor: Actor = ActorDep, session: AsyncSession = SessionDep):
    allow(actor, "catalog:read")
    await svc.item(session, item_id)
    return (await session.scalars(select(InventoryLot).where(InventoryLot.item_id == item_id).order_by(InventoryLot.code, InventoryLot.id).offset(offset).limit(limit))).all()


@router.post("/movements", response_model=MovementRead, status_code=201)
async def movement(payload: MovementCreate, actor: Actor = ActorDep, session: AsyncSession = SessionDep):
    async with session.begin():
        return await svc.movement(session, actor, payload)


@router.post("/movements/{movement_id}/correction", response_model=MovementRead, status_code=201)
async def correction(movement_id: UUID, payload: ReasonRequest, actor: Actor = ActorDep, session: AsyncSession = SessionDep):
    async with session.begin():
        return await svc.correct(session, actor, movement_id, payload.reason)


@router.get("/items/{item_id}/stock", response_model=StockRead)
async def stock(item_id: UUID, clinic_id: UUID, lot_id: UUID | None = None, actor: Actor = ActorDep, session: AsyncSession = SessionDep):
    return await svc.stock(session, actor, item_id, clinic_id, lot_id)


@router.get("/items/{item_id}/movements", response_model=list[MovementRead])
async def history(item_id: UUID, clinic_id: UUID, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100), actor: Actor = ActorDep, session: AsyncSession = SessionDep):
    allow(actor, "history:read")
    await svc.history_clinic(session, actor, clinic_id)
    await svc.item(session, item_id)
    query = select(InventoryMovement).where(InventoryMovement.item_id == item_id, InventoryMovement.clinic_id == clinic_id).order_by(InventoryMovement.occurred_at, InventoryMovement.id).offset(offset).limit(limit)
    if actor.role in {INVENTORY_REGIONAL, INVENTORY_AUDITOR}:
        query = query.where(InventoryMovement.jurisdiction_id.in_(actor.jurisdiction_ids))
    values = (await session.scalars(query)).all()
    return [MovementRead.model_validate(v).model_copy(update={"reason": "[REDACTED]" if v.reason is not None else None}) for v in values]


def scoped_query(actor):
    query = select(InventoryClinicItem).join(Clinic, Clinic.id == InventoryClinicItem.clinic_id).where(Clinic.is_active.is_(True))
    if actor.role in {INVENTORY_OPERATOR, INVENTORY_MANAGER}:
        return query.where(Clinic.id.in_(actor.clinic_ids))
    return query.where(Clinic.jurisdiction_id.in_(actor.jurisdiction_ids))


@router.get("/stock", response_model=list[StockRead])
async def regional_stock(clinic_id: UUID | None = None, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100), actor: Actor = ActorDep, session: AsyncSession = SessionDep):
    allow(actor, "stock:read")
    query = scoped_query(actor)
    if clinic_id:
        await svc.clinic(session, actor, clinic_id)
        query = query.where(InventoryClinicItem.clinic_id == clinic_id)
    configs = (await session.scalars(query.order_by(InventoryClinicItem.clinic_id, InventoryClinicItem.item_id).offset(offset).limit(limit))).all()
    return [await svc.stock(session, actor, c.item_id, c.clinic_id) for c in configs]


@router.get("/reorder", response_model=list[StockRead])
async def reorder(clinic_id: UUID | None = None, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100), actor: Actor = ActorDep, session: AsyncSession = SessionDep):
    allow(actor, "stock:read")
    totals = select(InventoryMovement.item_id, InventoryMovement.clinic_id, func.sum(InventoryMovement.delta).label("amount")).group_by(InventoryMovement.item_id, InventoryMovement.clinic_id).subquery()
    from sqlalchemy import and_
    query = scoped_query(actor).join(InventoryItem, InventoryItem.id == InventoryClinicItem.item_id).where(InventoryItem.is_active.is_(True)).outerjoin(totals, and_(totals.c.item_id == InventoryClinicItem.item_id, totals.c.clinic_id == InventoryClinicItem.clinic_id)).where(func.coalesce(totals.c.amount, 0) < InventoryClinicItem.reorder_point)
    if clinic_id:
        await svc.clinic(session, actor, clinic_id)
        query = query.where(InventoryClinicItem.clinic_id == clinic_id)
    # Recheck each result so concurrent changes cannot return a non-reorder item.
    configs = (await session.scalars(query.order_by(InventoryClinicItem.clinic_id, InventoryClinicItem.item_id).offset(offset).limit(limit))).all()
    return [s for c in configs if (s := await svc.stock(session, actor, c.item_id, c.clinic_id)).below_reorder]


@router.get("/items/{item_id}/audit", response_model=list[AuditRead])
async def audit(item_id: UUID, clinic_id: UUID, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100), actor: Actor = ActorDep, session: AsyncSession = SessionDep):
    allow(actor, "audit:read")
    await svc.history_clinic(session, actor, clinic_id)
    await svc.item(session, item_id)
    query = select(InventoryAudit).where(InventoryAudit.item_id == item_id, (InventoryAudit.clinic_id == clinic_id) | InventoryAudit.clinic_id.is_(None)).order_by(InventoryAudit.occurred_at, InventoryAudit.id).offset(offset).limit(limit)
    query = query.where(InventoryAudit.jurisdiction_id.in_(actor.jurisdiction_ids) | InventoryAudit.clinic_id.is_(None))
    values = (await session.scalars(query)).all()
    # Match the existing audit-read policy without changing historical data.
    return [AuditRead.model_validate(v).model_copy(update={"before_data": {"_redacted": True} if v.before_data is not None else None, "after_data": {"_redacted": True} if v.after_data is not None else None, "reason": "[REDACTED]" if v.reason is not None else None}) for v in values]


@router.get("/access-denials", response_model=list[AccessDenialRead])
async def access_denials(clinic_id: UUID | None = None, offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100), actor: Actor = ActorDep, session: AsyncSession = SessionDep):
    allow(actor, "audit:read")
    query = select(InventoryAccessDenial).where(
        InventoryAccessDenial.jurisdiction_id.in_(actor.jurisdiction_ids) |
        (InventoryAccessDenial.jurisdiction_id.is_(None) & (InventoryAccessDenial.actor_id == actor.id)))
    if clinic_id:
        query = query.where(InventoryAccessDenial.clinic_id == clinic_id)
    return (await session.scalars(query.order_by(InventoryAccessDenial.occurred_at,
        InventoryAccessDenial.id).offset(offset).limit(limit))).all()
