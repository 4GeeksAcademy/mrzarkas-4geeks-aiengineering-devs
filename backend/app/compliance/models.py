from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class ComplianceReview(Base):
    __tablename__ = "compliance_review"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    review_identifier: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    jurisdiction_id: Mapped[UUID] = mapped_column(ForeignKey("reference_jurisdiction.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by: Mapped[UUID] = mapped_column(nullable=False)
