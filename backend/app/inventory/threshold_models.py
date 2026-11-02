"""Internal threshold tracking; never an alternative stock balance."""
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.inventory.models import now


class InventoryThresholdState(Base):
    __tablename__ = 'inventory_threshold_state'
    __table_args__ = (CheckConstraint('threshold > 0', name='inventory_threshold_state_positive'),)
    item_id: Mapped[UUID] = mapped_column(ForeignKey('inventory_item.id'), primary_key=True)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey('reference_clinic.id'), primary_key=True)
    threshold: Mapped[int] = mapped_column(BigInteger)
    episode_id: Mapped[UUID | None] = mapped_column()


class InventoryThresholdTransition(Base):
    __tablename__ = 'inventory_threshold_transition'
    __table_args__ = (
        CheckConstraint("kind IN ('activated', 'cleared')", name='inventory_threshold_transition_kind'),
        CheckConstraint('threshold > 0', name='inventory_threshold_transition_positive'),
        Index('ix_inventory_threshold_episode_time', 'episode_id', 'occurred_at', 'id'),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    episode_id: Mapped[UUID] = mapped_column()
    movement_id: Mapped[UUID] = mapped_column(ForeignKey('inventory_movement.id'), unique=True)
    kind: Mapped[str] = mapped_column(String(20))
    threshold: Mapped[int] = mapped_column(BigInteger)
    jurisdiction_id: Mapped[UUID] = mapped_column(ForeignKey('reference_jurisdiction.id'))
    jurisdiction_key: Mapped[str] = mapped_column(String(100))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
