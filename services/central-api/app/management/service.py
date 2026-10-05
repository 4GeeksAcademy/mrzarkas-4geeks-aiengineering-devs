from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.management.audit import ManagementAuditEvent


def now_utc() -> datetime:
    return datetime.now(UTC)


def add_audit_event(
    session: AsyncSession,
    *,
    resource_type: str,
    resource_id: UUID,
    action: str,
    actor_id: UUID,
    before_data: dict | None,
    after_data: dict | None,
    reason: str | None = None,
) -> None:
    """Append an audit record to the caller's transaction."""
    session.add(ManagementAuditEvent(resource_type=resource_type, resource_id=resource_id, action=action, actor_id=actor_id, before_data=before_data, after_data=after_data, reason=reason, correlation_id=uuid4(), occurred_at=now_utc()))
