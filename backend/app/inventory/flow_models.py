"""Internal UI flow lifecycle; no stock, form contents or credentials."""
from datetime import datetime
from uuid import UUID
from sqlalchemy import String, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class InventoryTelemetryFlow(Base):
    __tablename__ = 'inventory_telemetry_flow'
    __table_args__ = (
        CheckConstraint("status IN ('open','completed','abandoned','uncertain')", name='inventory_flow_status'),
        CheckConstraint("last_step IN ('selection','validation','confirmation')", name='inventory_flow_step'),
        CheckConstraint("direction IS NULL OR direction IN ('inbound','outbound')", name='inventory_flow_direction'),
        Index('ix_inventory_flow_due', 'status', 'last_activity_at', 'flow_id'),
    )
    flow_id: Mapped[str] = mapped_column(String(67), primary_key=True)
    actor_id: Mapped[UUID] = mapped_column()
    item_id: Mapped[UUID] = mapped_column(ForeignKey('inventory_item.id'))
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey('reference_clinic.id'))
    jurisdiction_id: Mapped[UUID] = mapped_column(ForeignKey('reference_jurisdiction.id'))
    jurisdiction_key: Mapped[str] = mapped_column(String(100))
    environment: Mapped[str] = mapped_column(String(20))
    key_version: Mapped[str] = mapped_column(String(100))
    direction: Mapped[str | None] = mapped_column(String(20))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_step: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
