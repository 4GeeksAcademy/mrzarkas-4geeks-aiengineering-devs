from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Index, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


def now():
    return datetime.now(UTC)


class InventoryItem(Base):
    __tablename__ = "inventory_item"
    __table_args__ = (CheckConstraint("pack_size > 0", name="inventory_pack_positive"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(200))
    product_code: Mapped[str] = mapped_column(String(100), unique=True)
    unit: Mapped[str] = mapped_column(String(80))
    uses_lots: Mapped[bool] = mapped_column(Boolean, default=False)
    pack_label: Mapped[str | None] = mapped_column(String(80))
    pack_size: Mapped[int] = mapped_column(BigInteger, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    created_by: Mapped[UUID] = mapped_column()


class InventoryClinicItem(Base):
    __tablename__ = "inventory_clinic_item"
    __table_args__ = (CheckConstraint("reorder_point > 0", name="inventory_reorder_positive"),)
    item_id: Mapped[UUID] = mapped_column(ForeignKey("inventory_item.id"), primary_key=True)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("reference_clinic.id"), primary_key=True)
    reorder_point: Mapped[int] = mapped_column(BigInteger)


class InventoryLot(Base):
    __tablename__ = "inventory_lot"
    __table_args__ = (UniqueConstraint("item_id", "code", name="inventory_lot_code_unique"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    item_id: Mapped[UUID] = mapped_column(ForeignKey("inventory_item.id"))
    code: Mapped[str] = mapped_column(String(100))


class InventoryMovement(Base):
    __tablename__ = "inventory_movement"
    __table_args__ = (
        CheckConstraint("kind IN ('in', 'out', 'adjust', 'correction')", name="inventory_movement_kind"),
        CheckConstraint("pack_size > 0", name="inventory_movement_pack_positive"),
        CheckConstraint("(kind != 'in' OR delta > 0) AND (kind != 'out' OR delta < 0)", name="inventory_movement_sign"),
        CheckConstraint("counted_quantity IS NULL OR counted_quantity >= 0", name="inventory_count_nonnegative"),
        Index("ix_inventory_movement_scope_time", "item_id", "clinic_id", "occurred_at", "id"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    item_id: Mapped[UUID] = mapped_column(ForeignKey("inventory_item.id"))
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("reference_clinic.id"))
    lot_id: Mapped[UUID | None] = mapped_column(ForeignKey("inventory_lot.id"))
    kind: Mapped[str] = mapped_column(String(20))
    delta: Mapped[int] = mapped_column(BigInteger)
    unit: Mapped[str] = mapped_column(String(80))
    pack_label: Mapped[str | None] = mapped_column(String(80))
    pack_size: Mapped[int] = mapped_column(BigInteger)
    previous_quantity: Mapped[int] = mapped_column(BigInteger)
    counted_quantity: Mapped[int | None] = mapped_column(BigInteger)
    correction_of: Mapped[UUID | None] = mapped_column(ForeignKey("inventory_movement.id"), unique=True)
    reason: Mapped[str | None] = mapped_column(String(500))
    jurisdiction_id: Mapped[UUID | None] = mapped_column(ForeignKey("reference_jurisdiction.id"))
    jurisdiction_key: Mapped[str | None] = mapped_column(String(100))
    result: Mapped[str] = mapped_column(String(20), default="accepted")
    actor_id: Mapped[UUID] = mapped_column()
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class InventoryAudit(Base):
    __tablename__ = "inventory_audit"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    item_id: Mapped[UUID] = mapped_column(ForeignKey("inventory_item.id"))
    clinic_id: Mapped[UUID | None] = mapped_column(ForeignKey("reference_clinic.id"))
    jurisdiction_id: Mapped[UUID | None] = mapped_column(ForeignKey("reference_jurisdiction.id"))
    jurisdiction_key: Mapped[str | None] = mapped_column(String(100))
    result: Mapped[str] = mapped_column(String(20), default="accepted")
    actor_id: Mapped[UUID] = mapped_column()
    action: Mapped[str] = mapped_column(String(40))
    before_data: Mapped[dict | None] = mapped_column(JSON)
    after_data: Mapped[dict | None] = mapped_column(JSON)
    reason: Mapped[str | None] = mapped_column(String(500))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class InventoryAccessDenial(Base):
    __tablename__ = "inventory_access_denial"
    __table_args__ = (
        CheckConstraint("result = 'denied'", name="inventory_denial_result"),
        Index("ix_inventory_denial_country_time", "jurisdiction_id", "occurred_at", "id"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    actor_id: Mapped[UUID] = mapped_column()
    operation: Mapped[str] = mapped_column(String(80))
    reason_code: Mapped[str] = mapped_column(String(20))
    result: Mapped[str] = mapped_column(String(20), default="denied")
    clinic_id: Mapped[UUID | None] = mapped_column(ForeignKey("reference_clinic.id"))
    item_id: Mapped[UUID | None] = mapped_column(ForeignKey("inventory_item.id"))
    jurisdiction_id: Mapped[UUID | None] = mapped_column(ForeignKey("reference_jurisdiction.id"))
    jurisdiction_key: Mapped[str | None] = mapped_column(String(100))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
