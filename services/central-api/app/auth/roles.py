"""Roles and capabilities for OperationalIncident.

Mirrors the capability matrix in
memory-bank/specs/OperationalIncident-initial-decisions.md. `admin` is not
defined in that matrix; it is retained as the technical administration and
support role (see memory-bank/discrepancies.md).
"""

from __future__ import annotations

TECHNOLOGY = "technology"
RESPONSIBLE_AREA = "responsibleArea"
COMPLIANCE = "compliance"
DIRECTION = "direction"
ADMIN = "admin"

ROLES = {TECHNOLOGY, RESPONSIBLE_AREA, COMPLIANCE, DIRECTION, ADMIN}

# Capabilities granted to the technical administrator. Management writes stay
# exclusive to this role until the M0 matrix is formally approved.
_BROAD_CAPABILITIES = {
    "incident:create",
    "incident:list",
    "incident:read",
    "incident:update",
    "incident:changeSeverity",
    "incident:transition",
    "incident:assign",
    "incident:close",
    "incident:reopen",
    "catalog:read",
    "catalog:manage",
    "referenceData:read",
    "referenceData:manage",
    "audit:read",
    "complianceReview:read",
    "complianceReview:manage",
}

CAPABILITIES: dict[str, set[str]] = {
    ADMIN: set(_BROAD_CAPABILITIES),
    TECHNOLOGY: {
        "incident:create",
        "incident:list",
        "incident:read",
        "incident:update",
        "incident:changeSeverity",
        "incident:transition",
        "incident:close",
        "catalog:read",
        "referenceData:read",
    },
    COMPLIANCE: {
        "incident:list",
        "incident:read",
        "audit:read",
        "catalog:read",
        "referenceData:read",
        "complianceReview:read",
        "complianceReview:manage",
    },
    DIRECTION: {
        "incident:list",
    },
    # A responsibleArea actor may create and update limited fields on
    # incidents in its own area, and close/cancel them. No general update,
    # assign, reopen or audit access by default.
    RESPONSIBLE_AREA: {
        "incident:create",
        "incident:list",
        "incident:read",
        "incident:updateOwnArea",
        "incident:close",
        "catalog:read",
        "referenceData:read",
    },
}

# Capabilities that, for the responsibleArea role, must be checked against
# the incident's responsible_area_id matching the actor's area_id.
AREA_SCOPED_CAPABILITIES = {
    "incident:create",
    "incident:read",
    "incident:updateOwnArea",
    "incident:close",
}


def has_capability(role: str, capability: str) -> bool:
    return capability in CAPABILITIES.get(role, set())
