from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator, computed_field

from .retention import retention_deadline

Text = Annotated[str, Field(min_length=1, max_length=200)]
Code = Annotated[str, Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")]
Unit = Annotated[str, Field(min_length=1, max_length=80)]
Positive = Annotated[int, Field(strict=True, gt=0, le=1_000_000_000)]
Count = Annotated[int, Field(strict=True, ge=0, le=1_000_000_000)]
Reason = Annotated[str, Field(min_length=1, max_length=500)]


class Schema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, from_attributes=True)


class ItemCreate(Schema):
    title: Text
    product_code: Code
    unit: Unit
    uses_lots: bool = False
    pack_label: Unit | None = None
    pack_size: Positive = 1

    @model_validator(mode="after")
    def presentation(self):
        if self.pack_label is None and self.pack_size != 1:
            raise ValueError("A pack label is required for a pack size other than one")
        return self


class ItemUpdate(Schema):
    title: Text | None = None
    pack_label: Unit | None = None
    pack_size: Positive | None = None

    @model_validator(mode="after")
    def nonnull(self):
        if any(getattr(self, name) is None for name in self.model_fields_set - {"pack_label"}):
            raise ValueError("Editable attributes cannot be null")
        if not self.model_fields_set:
            raise ValueError("At least one attribute is required")
        return self


class ItemRead(ItemCreate):
    id: UUID
    is_active: bool
    created_by: UUID
    created_at: datetime


class ReasonRequest(Schema):
    reason: Reason


class ClinicConfig(Schema):
    reorder_point: Positive


class ClinicConfigRead(ClinicConfig):
    item_id: UUID
    clinic_id: UUID


class LotCreate(Schema):
    code: Code


class LotRead(LotCreate):
    id: UUID
    item_id: UUID


class MovementCreate(Schema):
    item_id: UUID
    clinic_id: UUID
    lot_id: UUID | None = None
    kind: Literal["in", "out", "adjust"]
    quantity: Positive | None = None
    counted_quantity: Count | None = None
    unit: Literal["base", "pack"] = "base"
    reason: Reason | None = None

    @model_validator(mode="after")
    def semantics(self):
        if self.kind == "adjust":
            if self.counted_quantity is None or self.quantity is not None or self.reason is None:
                raise ValueError("Adjustments require counted_quantity and reason, without quantity")
            if self.unit != "base":
                raise ValueError("Physical counts must use base units")
        elif self.quantity is None or self.counted_quantity is not None:
            raise ValueError("Entries and exits require quantity, without counted_quantity")
        return self


class EvidenceRead(Schema):
    occurred_at: datetime

    @computed_field
    @property
    def retention_until(self) -> datetime:
        return retention_deadline(self.occurred_at)


class MovementRead(EvidenceRead):
    id: UUID
    item_id: UUID
    clinic_id: UUID
    lot_id: UUID | None
    kind: Literal["in", "out", "adjust", "correction"]
    delta: int
    unit: str
    pack_label: str | None
    pack_size: int
    previous_quantity: int
    counted_quantity: int | None

    @computed_field
    @property
    def resulting_quantity(self) -> int:
        return self.previous_quantity + self.delta

    correction_of: UUID | None
    reason: str | None
    jurisdiction_id: UUID | None
    jurisdiction_key: str | None
    result: Literal["accepted"]
    actor_id: UUID
    occurred_at: datetime


class StockRead(Schema):
    item_id: UUID
    clinic_id: UUID
    lot_id: UUID | None = None
    quantity: int
    unit: str
    pack_label: str | None
    pack_size: int
    complete_packs: int
    remaining_units: int
    reorder_point: int
    below_reorder: bool


class AuditRead(EvidenceRead):
    id: UUID
    item_id: UUID
    clinic_id: UUID | None
    jurisdiction_id: UUID | None
    jurisdiction_key: str | None
    result: Literal["accepted"]
    actor_id: UUID
    action: str
    before_data: dict | None
    after_data: dict | None
    reason: str | None
    occurred_at: datetime


class AccessDenialRead(EvidenceRead):
    id: UUID
    actor_id: UUID
    operation: str
    reason_code: Literal["permission", "scope"]
    result: Literal["denied"]
    clinic_id: UUID | None
    item_id: UUID | None
    jurisdiction_id: UUID | None
    jurisdiction_key: str | None
    occurred_at: datetime
