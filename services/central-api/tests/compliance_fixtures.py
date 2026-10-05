"""Synthetic ComplianceReview values reserved for integration tests.

They deliberately contain no clinic, patient, employee or case data.
"""

from datetime import UTC, datetime
from uuid import UUID


SYNTHETIC_COMPLIANCE_REVIEWS = {
    "us_open": {
        "id": UUID("00000000-0000-0000-0000-000000000401"),
        "review_identifier": "SYN-US-REVIEW-001",
        "jurisdiction_id": UUID("00000000-0000-0000-0000-000000000001"),
        "status": "open",
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
        "created_by": UUID("00000000-0000-0000-0000-000000000900"),
    },
    "uk_open": {
        "id": UUID("00000000-0000-0000-0000-000000000402"),
        "review_identifier": "SYN-UK-REVIEW-001",
        "jurisdiction_id": UUID("00000000-0000-0000-0000-000000000002"),
        "status": "open",
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
        "created_by": UUID("00000000-0000-0000-0000-000000000900"),
    },
}
