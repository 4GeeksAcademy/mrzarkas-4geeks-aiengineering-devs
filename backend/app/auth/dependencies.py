"""FastAPI dependencies for authentication and capability checks."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from jwt import ExpiredSignatureError

from app.telemetry.security_producer import mark_success, mark_failure, mark_denial
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.roles import AREA_SCOPED_CAPABILITIES, RESPONSIBLE_AREA, has_capability
from app.auth.security import InvalidTokenError, decode_access_token

_bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Actor:
    id: UUID
    role: str
    area_id: UUID | None = None
    clinic_ids: tuple[UUID, ...] = ()
    jurisdiction_ids: tuple[UUID, ...] = ()


async def get_current_actor(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    request: Request = None,
) -> Actor:
    if credentials is None:
        mark_failure(request, "missing")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    try:
        payload = decode_access_token(credentials.credentials)
    except InvalidTokenError as error:
        mark_failure(request, "expired" if isinstance(error.__cause__, ExpiredSignatureError) else "invalid")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {error}",
        ) from error

    try:
        area_id = payload.get("area_id")
        actor = Actor(
            id=UUID(payload["sub"]), role=payload["role"],
            area_id=UUID(area_id) if area_id else None,
            clinic_ids=tuple(UUID(value) for value in payload.get("clinic_ids", [])),
            jurisdiction_ids=tuple(UUID(value) for value in payload.get("jurisdiction_ids", [])),
        )
    except (KeyError, TypeError, ValueError) as error:
        mark_failure(request, "invalid")
        raise HTTPException(401, "Invalid identity claims") from error
    mark_success(request, actor, credentials.credentials, payload.get("exp"))
    return actor


def require_capability(capability: str):
    """Return a dependency that authorizes an actor for `capability`.

    For the responsibleArea role, area-scoped capabilities also require the
    caller to pass an `area_id` matching the incident's own area; that extra
    check happens in the router, since it needs the loaded incident.
    """

    async def dependency(actor: Actor = Depends(get_current_actor), request: Request = None) -> Actor:
        if not has_capability(actor.role, capability):
            mark_denial(request, actor, capability)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{actor.role}' lacks capability '{capability}'",
            )
        return actor

    return dependency


def ensure_area_scope(actor: Actor, capability: str, resource_area_id: UUID) -> None:
    """Compatibility wrapper; policies are the source of contextual rules."""
    from app.auth.policies import require_incident_area_scope

    require_incident_area_scope(actor, capability, resource_area_id)
