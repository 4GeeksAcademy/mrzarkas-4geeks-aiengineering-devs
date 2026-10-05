import asyncio
from uuid import uuid4

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient, Response

from app.auth.dependencies import Actor, ensure_area_scope
from app.auth.policies import authorize_compliance_review_read
from app.auth.router import TokenRequest, issue_token
from app.auth.roles import (
    ADMIN,
    COMPLIANCE,
    DIRECTION,
    RESPONSIBLE_AREA,
    TECHNOLOGY,
    has_capability,
)
from app.auth.security import InvalidTokenError, create_access_token, decode_access_token
from app.core.config import get_settings
from app.main import app


def _request(method: str, path: str, **kwargs: object) -> Response:
    async def request() -> Response:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(request())


def test_admin_has_every_documented_capability() -> None:
    for capability in (
        "incident:create",
        "incident:update",
        "incident:transition",
        "incident:assign",
        "catalog:read",
        "catalog:manage",
        "referenceData:read",
        "referenceData:manage",
        "audit:read",
        "complianceReview:read",
        "complianceReview:manage",
    ):
        assert has_capability(ADMIN, capability)


def test_responsible_area_has_scoped_update_but_not_general_update() -> None:
    assert has_capability(RESPONSIBLE_AREA, "incident:create")
    assert has_capability(RESPONSIBLE_AREA, "incident:updateOwnArea")
    assert has_capability(RESPONSIBLE_AREA, "incident:close")
    assert not has_capability(RESPONSIBLE_AREA, "incident:update")
    assert not has_capability(RESPONSIBLE_AREA, "incident:transition")
    assert not has_capability(RESPONSIBLE_AREA, "audit:read")


def test_compliance_can_manage_reviews_but_not_catalogs_or_reference_data() -> None:
    assert has_capability(COMPLIANCE, "audit:read")
    assert has_capability(COMPLIANCE, "catalog:read")
    assert has_capability(COMPLIANCE, "referenceData:read")
    assert has_capability(COMPLIANCE, "complianceReview:manage")
    assert not has_capability(COMPLIANCE, "catalog:manage")
    assert not has_capability(COMPLIANCE, "referenceData:manage")


def test_technology_cannot_manage_catalogs_or_assign() -> None:
    assert has_capability(TECHNOLOGY, "catalog:read")
    assert has_capability(TECHNOLOGY, "referenceData:read")
    assert not has_capability(TECHNOLOGY, "catalog:manage")
    assert not has_capability(TECHNOLOGY, "referenceData:manage")
    assert not has_capability(TECHNOLOGY, "incident:assign")


def test_management_capability_matrix_is_explicit_for_every_role() -> None:
    expected = {
        ADMIN: {"catalog:read", "catalog:manage", "referenceData:read", "referenceData:manage", "complianceReview:read", "complianceReview:manage"},
        TECHNOLOGY: {"catalog:read", "referenceData:read"},
        COMPLIANCE: {"catalog:read", "referenceData:read", "complianceReview:read", "complianceReview:manage"},
        RESPONSIBLE_AREA: {"catalog:read", "referenceData:read"},
        DIRECTION: set(),
    }
    management_capabilities = {
        "catalog:read", "catalog:manage", "referenceData:read", "referenceData:manage", "complianceReview:read", "complianceReview:manage",
    }
    for role, granted in expected.items():
        assert {capability for capability in management_capabilities if has_capability(role, capability)} == granted


def test_token_roundtrip_preserves_role_and_area() -> None:
    actor_id = uuid4()
    area_id = uuid4()
    token = create_access_token(actor_id, RESPONSIBLE_AREA, area_id)

    payload = decode_access_token(token)

    assert payload["sub"] == str(actor_id)
    assert payload["role"] == RESPONSIBLE_AREA
    assert payload["area_id"] == str(area_id)


def test_decode_rejects_tampered_token() -> None:
    token = create_access_token(uuid4(), ADMIN)
    with pytest.raises(InvalidTokenError):
        decode_access_token(token + "tampered")


def test_ensure_area_scope_blocks_other_areas() -> None:
    own_area = uuid4()
    other_area = uuid4()
    actor = Actor(id=uuid4(), role=RESPONSIBLE_AREA, area_id=own_area)

    ensure_area_scope(actor, "incident:close", own_area)

    with pytest.raises(HTTPException) as error:
        ensure_area_scope(actor, "incident:close", other_area)
    assert error.value.status_code == 403


def test_ensure_area_scope_is_a_no_op_for_non_area_roles() -> None:
    actor = Actor(id=uuid4(), role=ADMIN)
    ensure_area_scope(actor, "incident:close", uuid4())


def test_compliance_review_visibility_policy_is_restricted_by_role() -> None:
    authorize_compliance_review_read(Actor(id=uuid4(), role=ADMIN))
    authorize_compliance_review_read(Actor(id=uuid4(), role=COMPLIANCE))

    for role in (TECHNOLOGY, RESPONSIBLE_AREA, DIRECTION):
        with pytest.raises(HTTPException) as error:
            authorize_compliance_review_read(Actor(id=uuid4(), role=role))
        assert error.value.status_code == 403


def test_self_issued_tokens_are_disabled_outside_development(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENVIRONMENT", "production")
    get_settings.cache_clear()
    try:
        with pytest.raises(HTTPException) as error:
            issue_token(TokenRequest(actor_id=uuid4(), role=ADMIN))
        assert error.value.status_code == 404
    finally:
        get_settings.cache_clear()


def test_token_endpoint_is_not_exposed_in_production(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENVIRONMENT", "production")
    get_settings.cache_clear()
    try:
        response = _request(
            "POST",
            "/auth/tokens",
            json={"actor_id": str(uuid4()), "role": ADMIN},
        )
        assert response.status_code == 404
    finally:
        get_settings.cache_clear()


def test_incident_routes_reject_missing_or_invalid_bearer_token() -> None:
    assert _request("GET", "/incidents").status_code == 401
    assert _request(
        "GET", "/incidents", headers={"Authorization": "Bearer invalid"}
    ).status_code == 401


def test_management_openapi_contract_exposes_administration_routes() -> None:
    paths = app.openapi()["paths"]
    assert "/management/catalogs" in paths
    assert "/management/reference-data/{resource}" in paths
    assert "/management/audit-events" in paths
    assert "/compliance-reviews/{review_id}/status" in paths
