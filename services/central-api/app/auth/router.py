"""Temporary dev token issuance. Replace with the client's SSO before any
non-development deployment (see memory-bank/proposals.md)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.auth.roles import ROLES
from app.auth.security import create_access_token
from app.core.config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])


class TokenRequest(BaseModel):
    actor_id: UUID
    role: str
    area_id: UUID | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/tokens", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def issue_token(payload: TokenRequest) -> TokenResponse:
    if not get_settings().self_issued_token_endpoint_enabled:
        # Deliberately return 404 rather than advertise a development-only
        # privilege-escalation endpoint in shared environments.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )
    if payload.role not in ROLES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown role: {payload.role}",
        )
    token = create_access_token(payload.actor_id, payload.role, payload.area_id)
    return TokenResponse(access_token=token)
