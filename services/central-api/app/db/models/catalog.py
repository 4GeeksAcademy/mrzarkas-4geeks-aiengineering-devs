from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Catalog(Base):
    __tablename__ = "catalog"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    catalog_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by: Mapped[UUID] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_by: Mapped[UUID] = mapped_column(nullable=False)

    values: Mapped[list[CatalogValue]] = relationship(
        back_populates="catalog", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("version > 0", name="ck_catalog_version_positive"),
    )


class CatalogValue(Base):
    __tablename__ = "catalog_value"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    catalog_id: Mapped[UUID] = mapped_column(ForeignKey("catalog.id"), nullable=False)
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_open: Mapped[bool | None] = mapped_column(Boolean)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by: Mapped[UUID] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_by: Mapped[UUID] = mapped_column(nullable=False)

    catalog: Mapped[Catalog] = relationship(back_populates="values")

    __table_args__ = (
        UniqueConstraint("catalog_id", "key", name="uq_catalog_value_catalog_key"),
        CheckConstraint("sort_order >= 0", name="ck_catalog_value_sort_order_nonnegative"),
        CheckConstraint(
            "effective_to IS NULL OR effective_to >= effective_from",
            name="ck_catalog_value_effective_range",
        ),
    )