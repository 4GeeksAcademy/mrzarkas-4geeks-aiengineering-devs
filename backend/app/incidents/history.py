from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IncidentStatusHistory(Base):
    __tablename__ = "incident_status_history"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    incident_id: Mapped[UUID] = mapped_column(ForeignKey("operational_incident.id", ondelete="CASCADE"), nullable=False)
    from_status_value_id: Mapped[UUID | None] = mapped_column(ForeignKey("catalog_value.id"))
    to_status_value_id: Mapped[UUID] = mapped_column(ForeignKey("catalog_value.id"), nullable=False)
    changed_by: Mapped[UUID] = mapped_column(nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class IncidentAssignmentHistory(Base):
    __tablename__ = "incident_assignment_history"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    incident_id: Mapped[UUID] = mapped_column(
        ForeignKey("operational_incident.id", ondelete="CASCADE"), nullable=False
    )
    from_responsible_area_id: Mapped[UUID | None] = mapped_column()
    to_responsible_area_id: Mapped[UUID] = mapped_column(nullable=False)
    changed_by: Mapped[UUID] = mapped_column(nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AuditEvent(Base):
    __tablename__ = "audit_event"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    actor_id: Mapped[UUID] = mapped_column(nullable=False)
    before_data: Mapped[dict | None] = mapped_column(JSON)
    after_data: Mapped[dict | None] = mapped_column(JSON)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
