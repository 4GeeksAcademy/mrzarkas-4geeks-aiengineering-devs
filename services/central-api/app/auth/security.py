"""Encode and verify the temporary self-issued JWTs.

Isolated on purpose: replacing this module with real SSO/OIDC verification
should not require changes in app.incidents or app.auth.dependencies beyond
how the token is validated.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from app.core.config import get_settings
from app.auth.roles import ROLES


class InvalidTokenError(Exception):
    """Raised when a bearer token is missing, malformed, or expired."""


def create_access_token(
    actor_id: UUID,
    role: str,
    area_id: UUID | None = None,
    expires_minutes: int | None = None,
) -> str:
    if role not in ROLES:
        raise ValueError(f"Unknown role: {role}")

    settings = get_settings()
    now = datetime.now(UTC)
    expires_delta = timedelta(minutes=expires_minutes or settings.jwt_expires_minutes)
    payload = {
        "sub": str(actor_id),
        "role": role,
        "area_id": str(area_id) if area_id else None,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    try:
        return jwt.decode(
            token,
            settings.jwt_secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError as error:
        raise InvalidTokenError(str(error)) from error
