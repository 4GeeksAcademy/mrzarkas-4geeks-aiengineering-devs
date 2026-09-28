from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.auth.dependencies import Actor, ensure_area_scope
from app.auth.roles import ADMIN, COMPLIANCE, RESPONSIBLE_AREA, TECHNOLOGY, has_capability
from app.auth.security import InvalidTokenError, create_access_token, decode_access_token


def test_admin_has_every_documented_capability() -> None:
    for capability in (
        "incident:create",
        "incident:update",
        "incident:transition",
        "incident:assign",
        "catalog:manage",
        "audit:read",
    ):
        assert has_capability(ADMIN, capability)


def test_responsible_area_is_limited_to_create_and_close() -> None:
    assert has_capability(RESPONSIBLE_AREA, "incident:create")
    assert has_capability(RESPONSIBLE_AREA, "incident:close")
    assert not has_capability(RESPONSIBLE_AREA, "incident:update")
    assert not has_capability(RESPONSIBLE_AREA, "incident:transition")
    assert not has_capability(RESPONSIBLE_AREA, "audit:read")


def test_compliance_can_read_audit_but_not_manage_catalogs() -> None:
    assert has_capability(COMPLIANCE, "audit:read")
    assert not has_capability(COMPLIANCE, "catalog:manage")


def test_technology_cannot_manage_catalogs_or_assign() -> None:
    assert not has_capability(TECHNOLOGY, "catalog:manage")
    assert not has_capability(TECHNOLOGY, "incident:assign")


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
