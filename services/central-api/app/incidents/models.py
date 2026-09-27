from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OperationalIncident(Base):
    __tablename__ = "operational_incident"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    incident_identifier: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    reporter_id: Mapped[UUID] = mapped_column(nullable=False)
    clinic_id: Mapped[UUID] = mapped_column(nullable=False)
    jurisdiction_id: Mapped[UUID] = mapped_column(nullable=False)
    affected_system_id: Mapped[UUID] = mapped_column(nullable=False)
    entry_channel_value_id: Mapped[UUID] = mapped_column(
        ForeignKey("catalog_value.id"), nullable=False
    )
    incident_type_value_id: Mapped[UUID] = mapped_column(
        ForeignKey("catalog_value.id"), nullable=False
    )
    severity_value_id: Mapped[UUID] = mapped_column(
        ForeignKey("catalog_value.id"), nullable=False
    )
    status_value_id: Mapped[UUID] = mapped_column(
        ForeignKey("catalog_value.id"), nullable=False
    )
    responsible_area_id: Mapped[UUID] = mapped_column(nullable=False)
    compliance_review_id: Mapped[UUID | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by: Mapped[UUID] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_by: Mapped[UUID] = mapped_column(nullable=False)

    __table_args__ = (
        UniqueConstraint("incident_identifier", name="uq_operational_incident_identifier"),
        Index("ix_operational_incident_status", "status_value_id"),
        Index("ix_operational_incident_severity", "severity_value_id"),
        Index("ix_operational_incident_area", "responsible_area_id"),
        Index("ix_operational_incident_created_at", "created_at"),
        Index("ix_operational_incident_updated_at", "updated_at"),
    )