from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CatalogListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    catalog_name: str
    version: int
    is_active: bool


class CatalogListResponse(BaseModel):
    items: list[CatalogListItem]
    total: int


class ManagedCatalogValueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    key: str
    label: str
    description: str | None
    is_active: bool
    is_open: bool | None
    sort_order: int
    effective_from: datetime
    effective_to: datetime | None
    created_at: datetime
    created_by: UUID
    updated_at: datetime
    updated_by: UUID


class CatalogValueListResponse(BaseModel):
    items: list[ManagedCatalogValueResponse]
    total: int


class CatalogValueCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str = Field(min_length=1, max_length=100, pattern=r"^[a-z][A-Za-z0-9]*$")
    label: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    is_open: bool | None = None
    sort_order: int = Field(default=0, ge=0)
    effective_from: datetime
    effective_to: datetime | None = None

    @model_validator(mode="after")
    def validate_effective_range(self) -> "CatalogValueCreate":
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("effective_to must be on or after effective_from")
        return self


class CatalogValueUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    is_open: bool | None = None
    sort_order: int | None = Field(default=None, ge=0)
    effective_from: datetime | None = None
    effective_to: datetime | None = None

    @model_validator(mode="after")
    def validate_effective_range(self) -> "CatalogValueUpdate":
        if (
            self.effective_from is not None
            and self.effective_to is not None
            and self.effective_to < self.effective_from
        ):
            raise ValueError("effective_to must be on or after effective_from")
        return self


class ActivationRequest(BaseModel):
    is_active: bool
    reason: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def require_reason_for_deactivation(self) -> "ActivationRequest":
        if not self.is_active and not self.reason:
            raise ValueError("reason is required when deactivating a catalog value")
        return self


class ReferenceValueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    key: str
    label: str
    is_active: bool
    created_at: datetime
    created_by: UUID
    updated_at: datetime
    updated_by: UUID
    jurisdiction_id: UUID | None = None


class ReferenceValueListResponse(BaseModel):
    items: list[ReferenceValueResponse]
    total: int


class ReferenceValueCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str = Field(min_length=1, max_length=100, pattern=r"^[a-z][A-Za-z0-9-]*$")
    label: str = Field(min_length=1, max_length=200)
    jurisdiction_id: UUID | None = None


class ReferenceValueUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str | None = Field(default=None, min_length=1, max_length=200)
    jurisdiction_id: UUID | None = None


class SystemJurisdictionsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    jurisdiction_ids: set[UUID]


class ManagementAuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    resource_type: str
    resource_id: UUID
    action: str
    actor_id: UUID
    before_data: dict | None
    after_data: dict | None
    reason: str | None
    correlation_id: UUID | None
    occurred_at: datetime


class ManagementAuditEventListResponse(BaseModel):
    items: list[ManagementAuditEventResponse]
    total: int
