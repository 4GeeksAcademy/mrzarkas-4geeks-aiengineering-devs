from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.reference_data.models import AffectedSystem, Clinic, Jurisdiction, ResponsibleArea, affected_system_jurisdiction


async def validate_incident_references(session: AsyncSession, clinic_id: UUID, jurisdiction_id: UUID, affected_system_id: UUID, responsible_area_id: UUID) -> None:
    clinic = await session.get(Clinic, clinic_id)
    jurisdiction = await session.get(Jurisdiction, jurisdiction_id)
    area = await session.get(ResponsibleArea, responsible_area_id)
    system = await session.get(AffectedSystem, affected_system_id)
    if not all((clinic, jurisdiction, area, system)) or not all((clinic.is_active, jurisdiction.is_active, area.is_active, system.is_active)):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invalid active incident reference")
    if clinic.jurisdiction_id != jurisdiction_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Clinic is not in the requested jurisdiction")
    coverage = await session.scalar(select(affected_system_jurisdiction).where(
        affected_system_jurisdiction.c.affected_system_id == affected_system_id,
        affected_system_jurisdiction.c.jurisdiction_id == jurisdiction_id,
    ))
    if coverage is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Affected system is not available in the requested jurisdiction")


async def validate_responsible_area(session: AsyncSession, responsible_area_id: UUID) -> None:
    area = await session.get(ResponsibleArea, responsible_area_id)
    if area is None or not area.is_active:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invalid active responsible area")
