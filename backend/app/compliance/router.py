from datetime import UTC, datetime
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import Actor, require_capability
from app.auth.policies import authorize_compliance_review_read
from app.db.session import get_session
from app.compliance.models import ComplianceReview
from app.reference_data.models import Jurisdiction
from app.management.service import add_audit_event

router = APIRouter(prefix="/compliance-reviews", tags=["compliance-reviews"])

class ComplianceReviewCreate(BaseModel):
    jurisdiction_id: UUID
    status: Literal["open", "inReview", "closed", "cancelled"] = "open"

class ComplianceReviewRead(ComplianceReviewCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    review_identifier: str
    created_at: datetime
    created_by: UUID


class ComplianceReviewStatusUpdate(BaseModel):
    status: Literal["open", "inReview", "closed", "cancelled"]
    reason: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def require_reason_for_closure(self) -> "ComplianceReviewStatusUpdate":
        if self.status in {"closed", "cancelled"} and not self.reason:
            raise ValueError("reason is required when closing a compliance review")
        return self

@router.post("", response_model=ComplianceReviewRead, status_code=status.HTTP_201_CREATED)
async def create_review(payload: ComplianceReviewCreate, session: AsyncSession = Depends(get_session), actor: Actor = Depends(require_capability("complianceReview:manage"))) -> ComplianceReview:
    jurisdiction = await session.get(Jurisdiction, payload.jurisdiction_id)
    if jurisdiction is None or not jurisdiction.is_active:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invalid active jurisdiction")
    now = datetime.now(UTC)
    review = ComplianceReview(review_identifier=f"CR-{now:%Y%m%d}-{uuid4().hex[:8].upper()}", jurisdiction_id=payload.jurisdiction_id, status=payload.status, created_at=now, created_by=actor.id)
    session.add(review)
    await session.flush()
    add_audit_event(
        session,
        resource_type="complianceReview",
        resource_id=review.id,
        action="created",
        actor_id=actor.id,
        before_data=None,
        after_data={"jurisdiction_id": str(review.jurisdiction_id), "status": review.status},
    )
    await session.commit()
    await session.refresh(review)
    return review

@router.get("/{review_id}", response_model=ComplianceReviewRead)
async def get_review(review_id: UUID, session: AsyncSession = Depends(get_session), actor: Actor = Depends(require_capability("complianceReview:read"))) -> ComplianceReview:
    authorize_compliance_review_read(actor)
    review = await session.get(ComplianceReview, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Compliance review not found")
    return review


@router.patch("/{review_id}/status", response_model=ComplianceReviewRead)
async def update_review_status(
    review_id: UUID,
    payload: ComplianceReviewStatusUpdate,
    session: AsyncSession = Depends(get_session),
    actor: Actor = Depends(require_capability("complianceReview:manage")),
) -> ComplianceReview:
    review = await session.get(ComplianceReview, review_id)
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compliance review not found")
    if review.status == payload.status:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Compliance review is already in that status")
    before = {"status": review.status}
    review.status = payload.status
    add_audit_event(
        session,
        resource_type="complianceReview",
        resource_id=review.id,
        action="statusChanged",
        actor_id=actor.id,
        before_data=before,
        after_data={"status": review.status},
        reason=payload.reason,
    )
    await session.commit()
    await session.refresh(review)
    return review
