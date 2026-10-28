from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import Actor, require_capability
from app.db.models.catalog import Catalog, CatalogValue
from app.db.session import get_session
from app.management.schemas import ActivationRequest, CatalogListResponse, CatalogValueCreate, CatalogValueListResponse, CatalogValueUpdate, ManagedCatalogValueResponse
from app.management.service import add_audit_event, now_utc
from app.reference_data.models import AffectedSystem, Clinic, Jurisdiction, ReferenceValue, ResponsibleArea, affected_system_jurisdiction
from app.incidents.models import OperationalIncident
from app.management.schemas import ManagementAuditEventListResponse, ReferenceValueCreate, ReferenceValueListResponse, ReferenceValueResponse, ReferenceValueUpdate, SystemJurisdictionsUpdate
from app.management.audit import ManagementAuditEvent


router = APIRouter(prefix="/management", tags=["management"])

REFERENCE_RESOURCES = {
    "jurisdictions": Jurisdiction,
    "clinics": Clinic,
    "affected-systems": AffectedSystem,
    "responsible-areas": ResponsibleArea,
}


def catalog_value_snapshot(value: CatalogValue) -> dict:
    return {"key": value.key, "label": value.label, "description": value.description, "is_active": value.is_active, "is_open": value.is_open, "sort_order": value.sort_order, "effective_from": value.effective_from.isoformat(), "effective_to": value.effective_to.isoformat() if value.effective_to else None}


async def get_catalog_or_404(session: AsyncSession, catalog_name: str) -> Catalog:
    catalog = (await session.execute(select(Catalog).where(Catalog.catalog_name == catalog_name))).scalar_one_or_none()
    if catalog is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Catalog not found")
    return catalog


async def get_catalog_value_or_404(session: AsyncSession, catalog: Catalog, value_id: UUID) -> CatalogValue:
    value = await session.get(CatalogValue, value_id)
    if value is None or value.catalog_id != catalog.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Catalog value not found")
    return value


def reference_snapshot(value: ReferenceValue) -> dict:
    snapshot = {"key": value.key, "label": value.label, "is_active": value.is_active}
    if isinstance(value, Clinic):
        snapshot["jurisdiction_id"] = str(value.jurisdiction_id)
    return snapshot


def reference_model_or_404(resource: str):
    model = REFERENCE_RESOURCES.get(resource)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference resource not found")
    return model


async def get_reference_or_404(session: AsyncSession, model, resource_id: UUID):
    value = await session.get(model, resource_id)
    if value is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference value not found")
    return value


async def validate_active_jurisdiction(session: AsyncSession, jurisdiction_id: UUID) -> Jurisdiction:
    jurisdiction = await session.get(Jurisdiction, jurisdiction_id)
    if jurisdiction is None or not jurisdiction.is_active:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid active jurisdiction")
    return jurisdiction


@router.get("/catalogs", response_model=CatalogListResponse)
async def list_catalogs(offset: int = Query(default=0, ge=0), limit: int = Query(default=50, ge=1, le=100), session: AsyncSession = Depends(get_session), actor: Actor = Depends(require_capability("catalog:read"))) -> CatalogListResponse:
    total = (await session.execute(select(func.count()).select_from(Catalog))).scalar_one()
    items = (await session.execute(select(Catalog).order_by(Catalog.catalog_name).offset(offset).limit(limit))).scalars().all()
    return CatalogListResponse(items=items, total=total)


@router.get("/catalogs/{catalog_name}/values", response_model=CatalogValueListResponse)
async def list_catalog_values(catalog_name: str, offset: int = Query(default=0, ge=0), limit: int = Query(default=50, ge=1, le=100), session: AsyncSession = Depends(get_session), actor: Actor = Depends(require_capability("catalog:read"))) -> CatalogValueListResponse:
    catalog = await get_catalog_or_404(session, catalog_name)
    filters = [CatalogValue.catalog_id == catalog.id]
    total = (await session.execute(select(func.count()).select_from(CatalogValue).where(*filters))).scalar_one()
    items = (await session.execute(select(CatalogValue).where(*filters).order_by(CatalogValue.sort_order, CatalogValue.key).offset(offset).limit(limit))).scalars().all()
    return CatalogValueListResponse(items=items, total=total)


@router.post("/catalogs/{catalog_name}/values", response_model=ManagedCatalogValueResponse, status_code=status.HTTP_201_CREATED)
async def create_catalog_value(catalog_name: str, payload: CatalogValueCreate, session: AsyncSession = Depends(get_session), actor: Actor = Depends(require_capability("catalog:manage"))) -> CatalogValue:
    catalog = await get_catalog_or_404(session, catalog_name)
    existing = (await session.execute(select(CatalogValue.id).where(CatalogValue.catalog_id == catalog.id, CatalogValue.key == payload.key))).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A catalog value with this key already exists")
    now = now_utc()
    value = CatalogValue(catalog_id=catalog.id, **payload.model_dump(), is_active=True, created_at=now, created_by=actor.id, updated_at=now, updated_by=actor.id)
    session.add(value)
    await session.flush()
    catalog.version += 1
    catalog.updated_at = now
    catalog.updated_by = actor.id
    add_audit_event(session, resource_type="catalogValue", resource_id=value.id, action="created", actor_id=actor.id, before_data=None, after_data=catalog_value_snapshot(value))
    await session.commit()
    await session.refresh(value)
    return value


@router.patch("/catalogs/{catalog_name}/values/{value_id}", response_model=ManagedCatalogValueResponse)
async def update_catalog_value(catalog_name: str, value_id: UUID, payload: CatalogValueUpdate, session: AsyncSession = Depends(get_session), actor: Actor = Depends(require_capability("catalog:manage"))) -> CatalogValue:
    catalog = await get_catalog_or_404(session, catalog_name)
    value = await get_catalog_value_or_404(session, catalog, value_id)
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        return value
    prospective_from = changes.get("effective_from", value.effective_from)
    prospective_to = changes.get("effective_to", value.effective_to)
    if prospective_to is not None and prospective_to < prospective_from:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="effective_to must be on or after effective_from")
    before = catalog_value_snapshot(value)
    for field, field_value in changes.items():
        setattr(value, field, field_value)
    now = now_utc()
    value.updated_at = now
    value.updated_by = actor.id
    catalog.version += 1
    catalog.updated_at = now
    catalog.updated_by = actor.id
    add_audit_event(session, resource_type="catalogValue", resource_id=value.id, action="updated", actor_id=actor.id, before_data=before, after_data=catalog_value_snapshot(value))
    await session.commit()
    await session.refresh(value)
    return value


@router.post("/catalogs/{catalog_name}/values/{value_id}/activation", response_model=ManagedCatalogValueResponse)
async def set_catalog_value_activation(catalog_name: str, value_id: UUID, payload: ActivationRequest, session: AsyncSession = Depends(get_session), actor: Actor = Depends(require_capability("catalog:manage"))) -> CatalogValue:
    catalog = await get_catalog_or_404(session, catalog_name)
    value = await get_catalog_value_or_404(session, catalog, value_id)
    before = catalog_value_snapshot(value)
    value.is_active = payload.is_active
    now = now_utc()
    value.updated_at = now
    value.updated_by = actor.id
    catalog.version += 1
    catalog.updated_at = now
    catalog.updated_by = actor.id
    add_audit_event(session, resource_type="catalogValue", resource_id=value.id, action="activated" if payload.is_active else "deactivated", actor_id=actor.id, before_data=before, after_data=catalog_value_snapshot(value), reason=payload.reason)
    await session.commit()
    await session.refresh(value)
    return value


@router.get("/reference-data/{resource}", response_model=ReferenceValueListResponse)
async def list_reference_values(resource: str, offset: int = Query(default=0, ge=0), limit: int = Query(default=50, ge=1, le=100), session: AsyncSession = Depends(get_session), actor: Actor = Depends(require_capability("referenceData:read"))) -> ReferenceValueListResponse:
    model = reference_model_or_404(resource)
    total = (await session.execute(select(func.count()).select_from(model))).scalar_one()
    items = (await session.execute(select(model).order_by(model.key).offset(offset).limit(limit))).scalars().all()
    return ReferenceValueListResponse(items=items, total=total)


@router.post("/reference-data/{resource}", response_model=ReferenceValueResponse, status_code=status.HTTP_201_CREATED)
async def create_reference_value(resource: str, payload: ReferenceValueCreate, session: AsyncSession = Depends(get_session), actor: Actor = Depends(require_capability("referenceData:manage"))) -> ReferenceValue:
    model = reference_model_or_404(resource)
    if resource == "clinics":
        if payload.jurisdiction_id is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="jurisdiction_id is required for clinics")
        await validate_active_jurisdiction(session, payload.jurisdiction_id)
    elif payload.jurisdiction_id is not None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="jurisdiction_id only applies to clinics")
    existing = (await session.execute(select(model.id).where(model.key == payload.key))).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A reference value with this key already exists")
    now = now_utc()
    data = payload.model_dump(exclude_none=True)
    value = model(**data, is_active=True, created_at=now, created_by=actor.id, updated_at=now, updated_by=actor.id)
    session.add(value)
    await session.flush()
    add_audit_event(session, resource_type=resource, resource_id=value.id, action="created", actor_id=actor.id, before_data=None, after_data=reference_snapshot(value))
    await session.commit()
    await session.refresh(value)
    return value


@router.patch("/reference-data/{resource}/{resource_id}", response_model=ReferenceValueResponse)
async def update_reference_value(resource: str, resource_id: UUID, payload: ReferenceValueUpdate, session: AsyncSession = Depends(get_session), actor: Actor = Depends(require_capability("referenceData:manage"))) -> ReferenceValue:
    model = reference_model_or_404(resource)
    value = await get_reference_or_404(session, model, resource_id)
    if resource == "clinics":
        changes = payload.model_dump(exclude_unset=True)
        new_jurisdiction_id = changes.get("jurisdiction_id")
        if new_jurisdiction_id is not None and new_jurisdiction_id != value.jurisdiction_id:
            await validate_active_jurisdiction(session, new_jurisdiction_id)
            incompatible_incident = await session.scalar(select(OperationalIncident.id).where(OperationalIncident.clinic_id == value.id, OperationalIncident.jurisdiction_id != new_jurisdiction_id).limit(1))
            if incompatible_incident is not None:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Clinic jurisdiction change would invalidate incident history")
    else:
        if payload.jurisdiction_id is not None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="jurisdiction_id only applies to clinics")
        changes = payload.model_dump(exclude_unset=True)
    if not changes:
        return value
    before = reference_snapshot(value)
    for field, field_value in changes.items():
        setattr(value, field, field_value)
    now = now_utc()
    value.updated_at = now
    value.updated_by = actor.id
    add_audit_event(session, resource_type=resource, resource_id=value.id, action="updated", actor_id=actor.id, before_data=before, after_data=reference_snapshot(value))
    await session.commit()
    await session.refresh(value)
    return value


@router.post("/reference-data/{resource}/{resource_id}/activation", response_model=ReferenceValueResponse)
async def set_reference_value_activation(resource: str, resource_id: UUID, payload: ActivationRequest, session: AsyncSession = Depends(get_session), actor: Actor = Depends(require_capability("referenceData:manage"))) -> ReferenceValue:
    model = reference_model_or_404(resource)
    value = await get_reference_or_404(session, model, resource_id)
    before = reference_snapshot(value)
    value.is_active = payload.is_active
    now = now_utc()
    value.updated_at = now
    value.updated_by = actor.id
    add_audit_event(session, resource_type=resource, resource_id=value.id, action="activated" if payload.is_active else "deactivated", actor_id=actor.id, before_data=before, after_data=reference_snapshot(value), reason=payload.reason)
    await session.commit()
    await session.refresh(value)
    return value


@router.put("/affected-systems/{system_id}/jurisdictions", response_model=list[UUID])
async def set_system_jurisdictions(system_id: UUID, payload: SystemJurisdictionsUpdate, session: AsyncSession = Depends(get_session), actor: Actor = Depends(require_capability("referenceData:manage"))) -> list[UUID]:
    system = await get_reference_or_404(session, AffectedSystem, system_id)
    requested = payload.jurisdiction_ids
    for jurisdiction_id in requested:
        await validate_active_jurisdiction(session, jurisdiction_id)
    current = set((await session.execute(select(affected_system_jurisdiction.c.jurisdiction_id).where(affected_system_jurisdiction.c.affected_system_id == system.id))).scalars().all())
    removed = current - requested
    if removed:
        historical_incident = await session.scalar(select(OperationalIncident.id).where(OperationalIncident.affected_system_id == system.id, OperationalIncident.jurisdiction_id.in_(removed)).limit(1))
        if historical_incident is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Coverage removal would invalidate incident history")
    before = {"jurisdiction_ids": sorted(str(value) for value in current)}
    if removed:
        await session.execute(affected_system_jurisdiction.delete().where(affected_system_jurisdiction.c.affected_system_id == system.id, affected_system_jurisdiction.c.jurisdiction_id.in_(removed)))
    added = requested - current
    if added:
        await session.execute(affected_system_jurisdiction.insert(), [{"affected_system_id": system.id, "jurisdiction_id": jurisdiction_id} for jurisdiction_id in added])
    now = now_utc()
    system.updated_at = now
    system.updated_by = actor.id
    add_audit_event(session, resource_type="affected-systems", resource_id=system.id, action="coverageChanged", actor_id=actor.id, before_data=before, after_data={"jurisdiction_ids": sorted(str(value) for value in requested)})
    await session.commit()
    return sorted(requested, key=str)


@router.get("/audit-events", response_model=ManagementAuditEventListResponse)
async def list_management_audit_events(
    resource_type: str | None = Query(default=None, max_length=100),
    resource_id: UUID | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    actor: Actor = Depends(require_capability("audit:read")),
) -> ManagementAuditEventListResponse:
    filters = []
    if resource_type:
        filters.append(ManagementAuditEvent.resource_type == resource_type)
    if resource_id:
        filters.append(ManagementAuditEvent.resource_id == resource_id)
    total = (
        await session.execute(
            select(func.count()).select_from(ManagementAuditEvent).where(*filters)
        )
    ).scalar_one()
    items = (
        await session.execute(
            select(ManagementAuditEvent)
            .where(*filters)
            .order_by(ManagementAuditEvent.occurred_at.desc())
            .offset(offset)
            .limit(limit)
        )
    ).scalars().all()
    return ManagementAuditEventListResponse(items=items, total=total)
