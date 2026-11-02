"""Approved calendar retention; no deletion or automatic purge is enabled."""
from calendar import monthrange
from datetime import UTC, datetime

APPROVAL_REFERENCE = "HC-INV-APPROVAL-2026-11-02"
RETENTION_MONTHS = 24


def retention_deadline(occurred_at: datetime) -> datetime:
    if occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
        raise ValueError("Retention requires a timezone-aware timestamp")
    occurred_at = occurred_at.astimezone(UTC)
    absolute_month = occurred_at.year * 12 + occurred_at.month - 1 + RETENTION_MONTHS
    year, month_zero = divmod(absolute_month, 12)
    month = month_zero + 1
    day = min(occurred_at.day, monthrange(year, month)[1])
    return occurred_at.replace(year=year, month=month, day=day)
