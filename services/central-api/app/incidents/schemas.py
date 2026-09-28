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


class IncidentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1, max_length=10000)
    severity_value_id: UUID | None = None
    responsible_area_id: UUID | None = None
    compliance_review_id: UUID | None = None


class StatusTransitionRequest(BaseModel):
    status_value_id: UUID
    reason: str | None = Field(default=None, max_length=2000)


class StatusHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    from_status_value_id: UUID | None
    to_status_value_id: UUID
    changed_by: UUID
    reason: str | None
    changed_at: datetime


class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    entity_type: str
    entity_id: UUID
    action: str
    actor_id: UUID
    before_data: dict | None
    after_data: dict | None
    occurred_at: datetime