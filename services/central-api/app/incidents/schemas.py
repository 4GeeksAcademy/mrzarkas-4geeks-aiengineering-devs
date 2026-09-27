from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class IncidentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=10000)
    reporter_id: UUID
    clinic_id: UUID
    jurisdiction_id: UUID
    affected_system_id: UUID
    entry_channel_value_id: UUID
    incident_type_value_id: UUID
    severity_value_id: UUID
    responsible_area_id: UUID
    compliance_review_id: UUID | None = None


class IncidentResponse(IncidentCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    incident_identifier: str
    status_value_id: UUID
    created_at: datetime
    created_by: UUID
    updated_at: datetime
    updated_by: UUID


class IncidentListResponse(BaseModel):
    items: list[IncidentResponse]
    total: int