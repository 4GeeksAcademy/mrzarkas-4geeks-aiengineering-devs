"""Approved synthetic-environment audit projections; never mutate storage."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AfterValidator, Field, StrictBool, StrictInt, StrictStr, TypeAdapter, ValidationError


REDACTED = "[REDACTED]"
WITHHELD = {"_redacted": True}


def redact_text(value: object) -> str | None:
    return None if value is None else REDACTED


def _uuid_string(value: str) -> str:
    UUID(value)
    return value


def _nullable_uuid_string(value: str) -> str:
    # Preserve the representation written by historical incident updates.
    return value if value == "None" else _uuid_string(value)


def _timestamp_string(value: str) -> str:
    datetime.fromisoformat(value)
    return value


UuidString = Annotated[StrictStr, AfterValidator(_uuid_string)]
NullableUuidString = Annotated[StrictStr, AfterValidator(_nullable_uuid_string)] | None
TimestampString = Annotated[StrictStr, AfterValidator(_timestamp_string)]
TechnicalKey = Annotated[StrictStr, Field(min_length=1, max_length=100, pattern=r"^[a-z][A-Za-z0-9-]*$")]
NonnegativeInt = Annotated[StrictInt, Field(ge=0)]
ReviewStatus = Literal["open", "inReview", "closed", "cancelled"]

# Each event has its own allowlist. Text fields are replaced before validation.
_catalog = {
    "key": TechnicalKey, "label": StrictStr | None, "description": StrictStr | None,
    "is_active": StrictBool, "is_open": StrictBool | None, "sort_order": NonnegativeInt,
    "effective_from": TimestampString, "effective_to": TimestampString | None,
}
_reference = {"key": TechnicalKey, "label": StrictStr | None, "is_active": StrictBool}
_incident_update = {
    "title": StrictStr | None, "description": StrictStr | None,
    "severity_value_id": UuidString, "responsible_area_id": UuidString,
    "compliance_review_id": NullableUuidString,
}
_policies: dict[tuple[str, str], dict] = {
    ("OperationalIncident", "created"): {"status_value_id": UuidString},
    ("OperationalIncident", "updated"): _incident_update,
    ("OperationalIncident", "status_changed"): {"status_value_id": UuidString},
    ("OperationalIncident", "assigned"): {"responsible_area_id": UuidString},
    ("affected-systems", "coverageChanged"): {"jurisdiction_ids": list[UuidString]},
    ("complianceReview", "created"): {"jurisdiction_id": UuidString, "status": ReviewStatus},
    ("complianceReview", "statusChanged"): {"status": ReviewStatus},
    ("complianceReview", "associated"): {"incident_id": UuidString},
    ("complianceReview", "disassociated"): {"incident_id": UuidString},
}
for _action in ("created", "updated", "activated", "deactivated"):
    _policies[("catalogValue", _action)] = _catalog
    for _resource in ("jurisdictions", "affected-systems", "responsible-areas"):
        _policies[(_resource, _action)] = _reference
    _policies[("clinics", _action)] = {**_reference, "jurisdiction_id": UuidString}

_adapters = {
    event: {field: TypeAdapter(field_type) for field, field_type in fields.items()}
    for event, fields in _policies.items()
}
_text_fields = {"title", "description", "label"}


def project_snapshot(resource: str, action: str, snapshot: object) -> dict | None:
    """Return a fresh allowlisted object, or an explicit withholding marker.

    Unknown/list-root snapshots are withheld rather than returned verbatim.
    Lists are allowed only in the known jurisdiction_ids projection. Invalid
    fields are omitted individually so valid transition references survive.
    """
    if snapshot is None:
        return None
    adapters = _adapters.get((resource, action))
    if adapters is None or not isinstance(snapshot, dict):
        return dict(WITHHELD)
    projected = {}
    redacted = False
    for field, value in snapshot.items():
        adapter = adapters.get(field)
        if adapter is None:
            redacted = True
            continue
        if field in _text_fields and value is not None:
            value = REDACTED
            redacted = True
        try:
            projected[field] = adapter.validate_python(value, strict=True)
        except (ValidationError, ValueError, TypeError):
            redacted = True
    if redacted:
        projected.update(WITHHELD)
    return projected
