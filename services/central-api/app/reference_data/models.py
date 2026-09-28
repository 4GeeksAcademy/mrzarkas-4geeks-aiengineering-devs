from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Table, Column
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ReferenceValue(Base):
    __abstract__ = True

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by: Mapped[UUID] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_by: Mapped[UUID] = mapped_column(nullable=False)


class Jurisdiction(ReferenceValue):
    __tablename__ = "reference_jurisdiction"


class ResponsibleArea(ReferenceValue):
    __tablename__ = "reference_responsible_area"


class AffectedSystem(ReferenceValue):
    __tablename__ = "reference_affected_system"


class Clinic(ReferenceValue):
    __tablename__ = "reference_clinic"

    jurisdiction_id: Mapped[UUID] = mapped_column(
        ForeignKey("reference_jurisdiction.id"), nullable=False
    )


affected_system_jurisdiction = Table(
    "reference_affected_system_jurisdiction",
    Base.metadata,
    Column("affected_system_id", ForeignKey("reference_affected_system.id"), primary_key=True),
    Column("jurisdiction_id", ForeignKey("reference_jurisdiction.id"), primary_key=True),
)
