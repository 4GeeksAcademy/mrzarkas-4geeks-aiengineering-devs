"""Roles and capabilities for OperationalIncident.

Mirrors the capability matrix in
memory-bank/specs/OperationalIncident-initial-decisions.md. `admin` is not
defined in that matrix; it was added as a technical role (see
memory-bank/discrepancies.md) and is not a functionally approved role.
"""

from __future__ import annotations

TECHNOLOGY = "technology"
RESPONSIBLE_AREA = "responsibleArea"
COMPLIANCE = "compliance"
DIRECTION = "direction"
ADMIN = "admin"

ROLES = {TECHNOLOGY, RESPONSIBLE_AREA, COMPLIANCE, DIRECTION, ADMIN}

# Capabilities granted to every role except responsibleArea, which is
# restricted below to create/close on its own area only.
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
    "catalog:manage",
    "audit:read",
    "complianceReview:read",
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
    },
    COMPLIANCE: {
        "incident:list",
        "incident:read",
        "audit:read",
        "complianceReview:read",
    },
    DIRECTION: {
        "incident:list",
    },
    # A responsibleArea actor may only create incidents for its own area
    # and close/cancel them (interpreted as the "borrado" action, since
    # incidents are never hard-deleted). No update, assign, reopen or
    # audit access by default.
    RESPONSIBLE_AREA: {
        "incident:create",
        "incident:list",
        "incident:read",
        "incident:close",
    },
}

# Capabilities that, for the responsibleArea role, must be checked against
# the incident's responsible_area_id matching the actor's area_id.
AREA_SCOPED_CAPABILITIES = {"incident:create", "incident:read", "incident:close"}


def has_capability(role: str, capability: str) -> bool:
    return capability in CAPABILITIES.get(role, set())
