from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.compliance.router import ComplianceReviewCreate, ComplianceReviewRead
from app.incidents.schemas import IncidentCreate, IncidentResponse
from app.main import app
from app.management.schemas import (
    CatalogValueListItem,
    ManagedCatalogValueResponse,
    ReferenceValueListItem,
    ReferenceValueResponse,
)


INCIDENT_FIELDS = {
    "title", "description", "clinic_id", "jurisdiction_id", "affected_system_id",
    "entry_channel_value_id", "incident_type_value_id", "severity_value_id",
    "responsible_area_id", "compliance_review_id", "id", "incident_identifier",
    "reporter_id", "status_value_id", "created_at", "created_by", "updated_at",
    "updated_by",
}
REVIEW_FIELDS = {
    "jurisdiction_id", "status", "id", "review_identifier", "created_at", "created_by",
}
CATALOG_FIELDS = {
    "id", "key", "label", "description", "is_active", "is_open", "sort_order",
    "effective_from", "effective_to", "created_at", "created_by", "updated_at",
    "updated_by",
}
REFERENCE_FIELDS = {
    "id", "key", "label", "is_active", "created_at", "created_by", "updated_at",
    "updated_by", "jurisdiction_id",
}


@pytest.mark.parametrize(
    ("model", "expected"),
    [
        (IncidentResponse, INCIDENT_FIELDS),
        (ComplianceReviewRead, REVIEW_FIELDS),
        (ManagedCatalogValueResponse, CATALOG_FIELDS),
        (CatalogValueListItem, CATALOG_FIELDS),
        (ReferenceValueResponse, REFERENCE_FIELDS),
        (ReferenceValueListItem, REFERENCE_FIELDS),
    ],
)
def test_orm_response_exposes_only_published_fields(model, expected) -> None:
    now = datetime.now(UTC)
    values = {field: uuid4() for field in expected}
    values.update({
        "title": "Synthetic incident", "description": "Synthetic description",
        "incident_identifier": "INC-SYNTHETIC", "review_identifier": "CR-SYNTHETIC",
        "status": "open", "key": "synthetic", "label": "Synthetic value",
        "is_active": True, "is_open": True, "sort_order": 0,
        "created_at": now, "updated_at": now, "effective_from": now,
        "effective_to": None, "internal_secret": "synthetic-hidden-marker",
    })
    # Simulate an ORM object gaining an internal column without a schema change.
    result = model.model_validate(SimpleNamespace(**values))
    assert set(result.model_dump(mode="json")) == expected
    assert "synthetic-hidden-marker" not in result.model_dump_json()


def test_read_contracts_do_not_inherit_write_contracts() -> None:
    assert not issubclass(IncidentResponse, IncidentCreate)
    assert not issubclass(ComplianceReviewRead, ComplianceReviewCreate)


@pytest.mark.parametrize(
    ("path", "method", "code", "schema"),
    [
        ("/incidents", "post", "201", "IncidentResponse"),
        ("/incidents/{incident_id}", "get", "200", "IncidentResponse"),
        ("/incidents/{incident_id}", "patch", "200", "IncidentResponse"),
        ("/incidents/{incident_id}/transitions", "post", "200", "IncidentResponse"),
        ("/incidents/{incident_id}/assignments", "post", "200", "IncidentResponse"),
        ("/compliance-reviews", "post", "201", "ComplianceReviewRead"),
        ("/compliance-reviews/{review_id}", "get", "200", "ComplianceReviewRead"),
        ("/compliance-reviews/{review_id}/status", "patch", "200", "ComplianceReviewRead"),
    ],
)
def test_domain_routes_keep_response_contract(path, method, code, schema) -> None:
    response = app.openapi()["paths"][path][method]["responses"][code]
    assert response["content"]["application/json"]["schema"] == {
        "$ref": f"#/components/schemas/{schema}"
    }
