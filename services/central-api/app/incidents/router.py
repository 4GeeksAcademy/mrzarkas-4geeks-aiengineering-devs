from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.catalog import Catalog, CatalogValue
from app.db.session import get_session
from app.incidents.models import OperationalIncident
from app.incidents.schemas import IncidentCreate, IncidentListResponse, IncidentResponse

router = APIRouter(prefix="/incidents", tags=["incidents"])


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
            .where(Catalog.catalog_name == "incidentStatus", CatalogValue.key == "new")
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