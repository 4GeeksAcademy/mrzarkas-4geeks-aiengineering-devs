"""Authorization policies for OperationalIncident resources.

FastAPI dependencies enforce a route's general capability. This module
enforces the contextual rules that need a loaded resource, such as area
ownership and the target of a state transition.
"""

from uuid import UUID

from fastapi import HTTPException, status

from app.auth.dependencies import Actor
from app.auth.roles import (
    ADMIN,
    AREA_SCOPED_CAPABILITIES,
    COMPLIANCE,
    RESPONSIBLE_AREA,
    has_capability,
)


RESPONSIBLE_AREA_CLOSE_STATUSES = {"closed", "cancelled"}


def visible_incident_area_id(actor: Actor) -> UUID | None:
    """Return the mandatory list scope for an actor, if one applies."""
    if actor.role != RESPONSIBLE_AREA:
        return None
    if actor.area_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A responsible area actor must have an assigned area",
        )
    return actor.area_id


def require_incident_area_scope(
    actor: Actor, capability: str, resource_area_id: UUID
) -> None:
    """Enforce resource-area isolation for area-scoped capabilities."""
    if actor.role != RESPONSIBLE_AREA or capability not in AREA_SCOPED_CAPABILITIES:
        return
    if actor.area_id != resource_area_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Actor is not authorized for this area",
        )


def authorize_status_transition(
    actor: Actor, responsible_area_id: UUID, target_status_key: str
) -> None:
    """Allow full transition capability or an area's own close/cancel action."""
    if has_capability(actor.role, "incident:transition"):
        return
    if (
        actor.role == RESPONSIBLE_AREA
        and has_capability(actor.role, "incident:close")
        and target_status_key in RESPONSIBLE_AREA_CLOSE_STATUSES
        and actor.area_id == responsible_area_id
    ):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Role '{actor.role}' cannot transition to '{target_status_key}'",
    )


def authorize_compliance_review_read(actor: Actor) -> None:
    """Apply the provisional visibility policy for ComplianceReview.

    Current JWTs do not carry a jurisdiction scope. Until M0 approves a more
    granular claim and its source of truth, only the global Compliance role
    and the technical administrator may view a review. The route-level
    capability check remains in place as a defence in depth measure.
    """
    if actor.role in {ADMIN, COMPLIANCE}:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Actor is not authorized to view compliance reviews",
    )
