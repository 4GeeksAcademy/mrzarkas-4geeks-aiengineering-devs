from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.catalog import Catalog, CatalogValue
from app.db.session import get_session
from app.incidents.history import AuditEvent, IncidentStatusHistory
from app.incidents.models import OperationalIncident
from app.incidents.schemas import (
    AuditEventResponse,
    IncidentCreate,
    IncidentListResponse,
    IncidentResponse,
    IncidentUpdate,
    StatusHistoryResponse,
    StatusTransitionRequest,
)

router = APIRouter(prefix="/incidents", tags=["incidents"])

ALLOWED_STATUS_TRANSITIONS = {
    "new": {"underAnalysis", "cancelled"},
    "underAnalysis": {"assigned", "inResolution", "onHold", "cancelled"},
    "assigned": {"inResolution", "onHold"},
    "inResolution": {"resolved", "onHold"},
    "resolved": {"reopened", "closed"},
    "onHold": {"underAnalysis", "assigned", "cancelled"},
    "reopened": {"underAnalysis"},
    "closed": set(),
    "cancelled": set(),
}


def make_incident_identifier() -> str:
    return f"HC-{datetime.now(UTC):%Y%m%d}-{uuid4().hex[:8].upper()}"


async def get_catalog_value(
    session: AsyncSession, value_id: UUID, catalog_name: str
) -> CatalogValue:
    value = (
        await session.execute(
            select(CatalogValue)
            .join(Catalog)
            .where(
                CatalogValue.id == value_id,
                Catalog.catalog_name == catalog_name,
                Catalog.is_active.is_(True),
                CatalogValue.is_active.is_(True),
            )
        )
    ).scalar_one_or_none()
    if value is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid active value for catalog {catalog_name}",
        )
    return value


@router.post("", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
async def create_incident(
    payload: IncidentCreate,
    session: AsyncSession = Depends(get_session),
) -> OperationalIncident:
    entry_channel = await get_catalog_value(session, payload.entry_channel_value_id, "entryChannel")
    incident_type = await get_catalog_value(session, payload.incident_type_value_id, "incidentType")
    severity = await get_catalog_value(session, payload.severity_value_id, "severity")

    new_status = (
        await session.execute(
            select(CatalogValue)
            .join(Catalog)
            .where(
                Catalog.catalog_name == "incidentStatus",
                CatalogValue.key == "new",
                Catalog.is_active.is_(True),
                CatalogValue.is_active.is_(True),
            )
        )
    ).scalar_one_or_none()
    if new_status is None:
        raise HTTPException(status_code=503, detail="Initial incident status is not configured")

    now = datetime.now(UTC)
    actor_id = payload.reporter_id
    incident = OperationalIncident(
        **payload.model_dump(),
        incident_identifier=make_incident_identifier(),
        status_value_id=new_status.id,
        created_at=now,
        created_by=actor_id,
        updated_at=now,
        updated_by=actor_id,
    )
    session.add(incident)
    await session.flush()
    session.add(IncidentStatusHistory(
        incident_id=incident.id,
        from_status_value_id=None,
        to_status_value_id=new_status.id,
        changed_by=actor_id,
        reason="Incident created",
        changed_at=now,
    ))
    session.add(AuditEvent(
        entity_type="OperationalIncident",
        entity_id=incident.id,
        action="created",
        actor_id=actor_id,
        before_data=None,
        after_data={"status_value_id": str(new_status.id)},
        occurred_at=now,
    ))
    await session.commit()
    await session.refresh(incident)
    return incident


@router.get("", response_model=IncidentListResponse)
async def list_incidents(
    status_value_id: UUID | None = Query(default=None),
    severity_value_id: UUID | None = Query(default=None),
    responsible_area_id: UUID | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> IncidentListResponse:
    filters = []
    if status_value_id:
        filters.append(OperationalIncident.status_value_id == status_value_id)
    if severity_value_id:
        filters.append(OperationalIncident.severity_value_id == severity_value_id)
    if responsible_area_id:
        filters.append(OperationalIncident.responsible_area_id == responsible_area_id)

    total = (await session.execute(select(func.count()).select_from(OperationalIncident).where(*filters))).scalar_one()
    items = (
        await session.execute(
            select(OperationalIncident)
            .where(*filters)
            .order_by(OperationalIncident.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
    ).scalars().all()
    return IncidentListResponse(items=items, total=total)


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: UUID, session: AsyncSession = Depends(get_session)
) -> OperationalIncident:
    incident = await session.get(OperationalIncident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.patch("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: UUID,
    payload: IncidentUpdate,
    session: AsyncSession = Depends(get_session),
) -> OperationalIncident:
    incident = await session.get(OperationalIncident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    changes = payload.model_dump(exclude_unset=True)
    if "severity_value_id" in changes:
        await get_catalog_value(session, changes["severity_value_id"], "severity")
    if not changes:
        return incident

    actor_id = changes.pop("actor_id", None) or incident.updated_by
    before = {key: str(getattr(incident, key)) for key in changes}
    for key, value in changes.items():
        setattr(incident, key, value)
    incident.updated_at = datetime.now(UTC)
    incident.updated_by = actor_id
    session.add(AuditEvent(
        entity_type="OperationalIncident", entity_id=incident.id, action="updated",
        actor_id=actor_id, before_data=before,
        after_data={key: str(value) for key, value in changes.items()},
        occurred_at=incident.updated_at,
    ))
    await session.commit()
    await session.refresh(incident)
    return incident


@router.post("/{incident_id}/transitions", response_model=IncidentResponse)
async def transition_incident(
    incident_id: UUID,
    payload: StatusTransitionRequest,
    session: AsyncSession = Depends(get_session),
) -> OperationalIncident:
    incident = await session.get(OperationalIncident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    target = await get_catalog_value(session, payload.status_value_id, "incidentStatus")
    current = await session.get(CatalogValue, incident.status_value_id)
    if current is None:
        raise HTTPException(status_code=500, detail="Current incident status is invalid")
    if current.id == target.id:
        raise HTTPException(status_code=409, detail="Incident is already in that status")
    if target.key not in ALLOWED_STATUS_TRANSITIONS.get(current.key, set()):
        raise HTTPException(
            status_code=409,
            detail=f"Transition from {current.key} to {target.key} is not allowed",
        )

    now = datetime.now(UTC)
    session.add(IncidentStatusHistory(
        incident_id=incident.id, from_status_value_id=current.id,
        to_status_value_id=target.id, changed_by=payload.actor_id,
        reason=payload.reason, changed_at=now,
    ))
    session.add(AuditEvent(
        entity_type="OperationalIncident", entity_id=incident.id, action="status_changed",
        actor_id=payload.actor_id, before_data={"status_value_id": str(current.id)},
        after_data={"status_value_id": str(target.id)}, occurred_at=now,
    ))
    incident.status_value_id = target.id
    incident.updated_at = now
    incident.updated_by = payload.actor_id
    await session.commit()
    await session.refresh(incident)
    return incident


@router.get("/{incident_id}/history", response_model=list[StatusHistoryResponse])
async def incident_history(incident_id: UUID, session: AsyncSession = Depends(get_session)) -> list[IncidentStatusHistory]:
    if await session.get(OperationalIncident, incident_id) is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return list((await session.execute(
        select(IncidentStatusHistory).where(IncidentStatusHistory.incident_id == incident_id).order_by(IncidentStatusHistory.changed_at)
    )).scalars().all())


@router.get("/{incident_id}/audit", response_model=list[AuditEventResponse])
async def incident_audit(incident_id: UUID, session: AsyncSession = Depends(get_session)) -> list[AuditEvent]:
    if await session.get(OperationalIncident, incident_id) is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return list((await session.execute(
        select(AuditEvent).where(AuditEvent.entity_type == "OperationalIncident", AuditEvent.entity_id == incident_id).order_by(AuditEvent.occurred_at)
    )).scalars().all())