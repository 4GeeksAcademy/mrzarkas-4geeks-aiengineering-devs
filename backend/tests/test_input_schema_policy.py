from uuid import uuid4

import pytest
from pydantic import BaseModel, ValidationError

from app.auth.router import TokenRequest
from app.compliance.router import ComplianceReviewCreate, ComplianceReviewStatusUpdate
from app.incidents.schemas import (
    IncidentAssignmentRequest,
    IncidentCreate,
    IncidentUpdate,
    StatusTransitionRequest,
)
from app.management.schemas import (
    ActivationRequest,
    CatalogValueCreate,
    CatalogValueUpdate,
    ReferenceValueCreate,
    ReferenceValueUpdate,
    SystemJurisdictionsUpdate,
)


@pytest.mark.parametrize(
    ("model", "payload"),
    [
        (TokenRequest, {"actor_id": str(uuid4()), "role": "admin"}),
        (ComplianceReviewCreate, {"jurisdiction_id": str(uuid4())}),
        (ComplianceReviewStatusUpdate, {"status": "open"}),
        (
            IncidentCreate,
            {
                "title": "Synthetic incident",
                "description": "Synthetic description",
                "clinic_id": str(uuid4()),
                "jurisdiction_id": str(uuid4()),
                "affected_system_id": str(uuid4()),
                "entry_channel_value_id": str(uuid4()),
                "incident_type_value_id": str(uuid4()),
                "severity_value_id": str(uuid4()),
                "responsible_area_id": str(uuid4()),
            },
        ),
        (IncidentUpdate, {"title": "Synthetic update"}),
        (StatusTransitionRequest, {"status_value_id": str(uuid4())}),
        (IncidentAssignmentRequest, {"responsible_area_id": str(uuid4())}),
        (ActivationRequest, {"is_active": True}),
    ],
)
def test_write_models_ignore_extra_fields(
    model: type[BaseModel], payload: dict[str, object]
) -> None:
    result = model.model_validate({**payload, "unexpected_field": "ignored"})

    assert not hasattr(result, "unexpected_field")


@pytest.mark.parametrize(
    ("model", "payload"),
    [
        (
            CatalogValueCreate,
            {
                "key": "syntheticValue",
                "label": "Synthetic value",
                "effective_from": "2026-10-31T00:00:00+00:00",
            },
        ),
        (CatalogValueUpdate, {"label": "Synthetic value"}),
        (ReferenceValueCreate, {"key": "synthetic-value", "label": "Synthetic value"}),
        (ReferenceValueUpdate, {"label": "Synthetic value"}),
        (SystemJurisdictionsUpdate, {"jurisdiction_ids": []}),
    ],
)
def test_write_models_forbid_extra_fields(
    model: type[BaseModel], payload: dict[str, object]
) -> None:
    with pytest.raises(ValidationError) as error:
        model.model_validate({**payload, "unexpected_field": "rejected"})

    assert any(item["type"] == "extra_forbidden" for item in error.value.errors())