from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import Actor, get_current_actor, require_capability
from app.auth.policies import (
    authorize_status_transition,
    require_incident_area_scope,
    visible_incident_area_id,
)
from app.auth.roles import has_capability
from app.db.models.catalog import Catalog, CatalogValue
from app.db.session import get_session
from app.incidents.history import AuditEvent, IncidentAssignmentHistory, IncidentStatusHistory
from app.incidents.models import OperationalIncident
from app.reference_data.validation import validate_incident_references, validate_responsible_area
from app.compliance.models import ComplianceReview
from app.management.service import add_audit_event
from app.incidents.schemas import (
    AuditEventResponse,
    AssignmentHistoryResponse,
    IncidentAssignmentRequest,
    IncidentCreate,
    IncidentListResponse,
    IncidentResponse,
    IncidentUpdate,
    OpenIncidentsBySeverityResponse,
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
    actor: Actor = Depends(require_capability("incident:create")),
) -> OperationalIncident:
    require_incident_area_scope(actor, "incident:create", payload.responsible_area_id)
    await validate_incident_references(session, payload.clinic_id, payload.jurisdiction_id, payload.affected_system_id, payload.responsible_area_id)
    if payload.compliance_review_id:
        review = await session.get(ComplianceReview, payload.compliance_review_id)
        if review is None or review.jurisdiction_id != payload.jurisdiction_id:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invalid compliance review for jurisdiction")

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
    incident = OperationalIncident(
        **payload.model_dump(exclude={"reporter_id"}),
        reporter_id=actor.id,
        incident_identifier=make_incident_identifier(),
        status_value_id=new_status.id,
        created_at=now,
        created_by=actor.id,
        updated_at=now,
        updated_by=actor.id,
    )
    session.add(incident)
    await session.flush()
    session.add(IncidentStatusHistory(
        incident_id=incident.id,
        from_status_value_id=None,
        to_status_value_id=new_status.id,
        changed_by=actor.id,
        reason="Incident created",
        changed_at=now,
    ))
    session.add(AuditEvent(
        entity_type="OperationalIncident",
        entity_id=incident.id,
        action="created",
        actor_id=actor.id,
        before_data=None,
        after_data={"status_value_id": str(new_status.id)},
        occurred_at=now,
    ))
    if payload.compliance_review_id:
        add_audit_event(
            session,
            resource_type="complianceReview",
            resource_id=payload.compliance_review_id,
            action="associated",
            actor_id=actor.id,
            before_data=None,
            after_data={"incident_id": str(incident.id)},
        )
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
    actor: Actor = Depends(require_capability("incident:list")),
) -> IncidentListResponse:
    filters = []
    if status_value_id:
        filters.append(OperationalIncident.status_value_id == status_value_id)
    if severity_value_id:
        filters.append(OperationalIncident.severity_value_id == severity_value_id)

    # A responsibleArea actor can only ever see its own area, regardless of
    # what was requested in the query string.
    scoped_area_id = visible_incident_area_id(actor)
    if scoped_area_id is not None:
        filters.append(OperationalIncident.responsible_area_id == scoped_area_id)
    elif responsible_area_id:
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


@router.get("/metrics/open-by-severity", response_model=list[OpenIncidentsBySeverityResponse])
async def open_incidents_by_severity(
    session: AsyncSession = Depends(get_session),
    actor: Actor = Depends(require_capability("incident:list")),
) -> list[OpenIncidentsBySeverityResponse]:
    severity_catalog = aliased(Catalog)
    severity_value = aliased(CatalogValue)

    rows = (await session.execute(
        select(
            severity_value.id,
            severity_value.key,
            severity_value.label,
        )
        .join(severity_catalog, severity_value.catalog_id == severity_catalog.id)
        .where(
            severity_catalog.catalog_name == "severity",
            severity_catalog.is_active.is_(True),
            severity_value.is_active.is_(True),
        )
        .group_by(severity_value.id, severity_value.key, severity_value.label)
        .order_by(severity_value.key)
    )).all()

    # Count only open incidents. Keeping this calculation in the API avoids
    # duplicating status semantics in future clients.
    status_value = aliased(CatalogValue)
    open_counts = dict((await session.execute(
        select(OperationalIncident.severity_value_id, func.count(OperationalIncident.id))
        .join(status_value, OperationalIncident.status_value_id == status_value.id)
        .where(status_value.is_open.is_(True))
        .group_by(OperationalIncident.severity_value_id)
    )).all())
    return [
        OpenIncidentsBySeverityResponse(
            severity_value_id=severity_id,
            severity_key=severity_key,
            severity_label=severity_label,
            open_incident_count=open_counts.get(severity_id, 0),
        )
        for severity_id, severity_key, severity_label in rows
    ]


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: UUID,
    session: AsyncSession = Depends(get_session),
    actor: Actor = Depends(require_capability("incident:read")),
) -> OperationalIncident:
    incident = await session.get(OperationalIncident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    require_incident_area_scope(actor, "incident:read", incident.responsible_area_id)
    return incident


@router.patch("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: UUID,
    payload: IncidentUpdate,
    session: AsyncSession = Depends(get_session),
    actor: Actor = Depends(require_capability("incident:update")),
) -> OperationalIncident:
    # Dependencies are not evaluated when this handler is called directly
    # from service/integration tests, so keep the authorization invariant in
    # the handler as well as in FastAPI's dependency graph.
    if not has_capability(actor.role, "incident:update"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{actor.role}' lacks capability 'incident:update'",
        )
    incident = await session.get(OperationalIncident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    require_incident_area_scope(actor, "incident:update", incident.responsible_area_id)

    changes = payload.model_dump(exclude_unset=True)
    if "severity_value_id" in changes:
        await get_catalog_value(session, changes["severity_value_id"], "severity")
    if "responsible_area_id" in changes:
        await validate_responsible_area(session, changes["responsible_area_id"])
    if "compliance_review_id" in changes and changes["compliance_review_id"]:
        review = await session.get(ComplianceReview, changes["compliance_review_id"])
        if review is None or review.jurisdiction_id != incident.jurisdiction_id:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invalid compliance review for jurisdiction")
    if not changes:
        return incident

    previous_compliance_review_id = incident.compliance_review_id
    before = {key: str(getattr(incident, key)) for key in changes}
    for key, value in changes.items():
        setattr(incident, key, value)
    incident.updated_at = datetime.now(UTC)
    incident.updated_by = actor.id
    session.add(AuditEvent(
        entity_type="OperationalIncident", entity_id=incident.id, action="updated",
        actor_id=actor.id, before_data=before,
        after_data={key: str(value) for key, value in changes.items()},
        occurred_at=incident.updated_at,
    ))
    if "compliance_review_id" in changes and previous_compliance_review_id != incident.compliance_review_id:
        if previous_compliance_review_id:
            add_audit_event(
                session,
                resource_type="complianceReview",
                resource_id=previous_compliance_review_id,
                action="disassociated",
                actor_id=actor.id,
                before_data={"incident_id": str(incident.id)},
                after_data=None,
            )
        if incident.compliance_review_id:
            add_audit_event(
                session,
                resource_type="complianceReview",
                resource_id=incident.compliance_review_id,
                action="associated",
                actor_id=actor.id,
                before_data=None,
                after_data={"incident_id": str(incident.id)},
            )
    await session.commit()
    await session.refresh(incident)
    return incident


@router.post("/{incident_id}/transitions", response_model=IncidentResponse)
async def transition_incident(
    incident_id: UUID,
    payload: StatusTransitionRequest,
    session: AsyncSession = Depends(get_session),
    actor: Actor = Depends(get_current_actor),
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
    authorize_status_transition(actor, incident.responsible_area_id, target.key)

    now = datetime.now(UTC)
    session.add(IncidentStatusHistory(
        incident_id=incident.id, from_status_value_id=current.id,
        to_status_value_id=target.id, changed_by=actor.id,
        reason=payload.reason, changed_at=now,
    ))
    session.add(AuditEvent(
        entity_type="OperationalIncident", entity_id=incident.id, action="status_changed",
        actor_id=actor.id, before_data={"status_value_id": str(current.id)},
        after_data={"status_value_id": str(target.id)}, occurred_at=now,
    ))
    incident.status_value_id = target.id
    incident.updated_at = now
    incident.updated_by = actor.id
    await session.commit()
    await session.refresh(incident)
    return incident


@router.post("/{incident_id}/assignments", response_model=IncidentResponse)
async def assign_incident(
    incident_id: UUID,
    payload: IncidentAssignmentRequest,
    session: AsyncSession = Depends(get_session),
    actor: Actor = Depends(require_capability("incident:assign")),
) -> OperationalIncident:
    incident = await session.get(OperationalIncident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    if incident.responsible_area_id == payload.responsible_area_id:
        raise HTTPException(status_code=409, detail="Incident is already assigned to that area")
    await validate_responsible_area(session, payload.responsible_area_id)

    now = datetime.now(UTC)
    previous_area_id = incident.responsible_area_id
    session.add(IncidentAssignmentHistory(
        incident_id=incident.id,
        from_responsible_area_id=previous_area_id,
        to_responsible_area_id=payload.responsible_area_id,
        changed_by=actor.id,
        reason=payload.reason,
        changed_at=now,
    ))
    session.add(AuditEvent(
        entity_type="OperationalIncident",
        entity_id=incident.id,
        action="assigned",
        actor_id=actor.id,
        before_data={"responsible_area_id": str(previous_area_id)},
        after_data={"responsible_area_id": str(payload.responsible_area_id)},
        occurred_at=now,
    ))
    incident.responsible_area_id = payload.responsible_area_id
    incident.updated_at = now
    incident.updated_by = actor.id
    await session.commit()
    await session.refresh(incident)
    return incident


@router.get("/{incident_id}/history", response_model=list[StatusHistoryResponse])
async def incident_history(
    incident_id: UUID,
    session: AsyncSession = Depends(get_session),
    actor: Actor = Depends(require_capability("incident:read")),
) -> list[IncidentStatusHistory]:
    incident = await session.get(OperationalIncident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    require_incident_area_scope(actor, "incident:read", incident.responsible_area_id)
    return list((await session.execute(
        select(IncidentStatusHistory).where(IncidentStatusHistory.incident_id == incident_id).order_by(IncidentStatusHistory.changed_at)
    )).scalars().all())


@router.get("/{incident_id}/assignment-history", response_model=list[AssignmentHistoryResponse])
async def incident_assignment_history(
    incident_id: UUID,
    session: AsyncSession = Depends(get_session),
    actor: Actor = Depends(require_capability("incident:read")),
) -> list[IncidentAssignmentHistory]:
    incident = await session.get(OperationalIncident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    require_incident_area_scope(actor, "incident:read", incident.responsible_area_id)
    return list((await session.execute(
        select(IncidentAssignmentHistory)
        .where(IncidentAssignmentHistory.incident_id == incident_id)
        .order_by(IncidentAssignmentHistory.changed_at)
    )).scalars().all())


@router.get("/{incident_id}/audit", response_model=list[AuditEventResponse])
async def incident_audit(
    incident_id: UUID,
    session: AsyncSession = Depends(get_session),
    actor: Actor = Depends(require_capability("audit:read")),
) -> list[AuditEvent]:
    if await session.get(OperationalIncident, incident_id) is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return list((await session.execute(
        select(AuditEvent).where(AuditEvent.entity_type == "OperationalIncident", AuditEvent.entity_id == incident_id).order_by(AuditEvent.occurred_at)
    )).scalars().all())
