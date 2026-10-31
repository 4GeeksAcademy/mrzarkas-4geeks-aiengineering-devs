import asyncio
from copy import deepcopy
from datetime import UTC, datetime
import os
from types import SimpleNamespace
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.audit_serialization import REDACTED, project_snapshot
from app.auth.security import create_access_token
from app.db.session import SessionLocal, engine, get_session
from app.db.models.catalog import CatalogValue
from app.incidents.history import AuditEvent, IncidentStatusHistory, IncidentAssignmentHistory
from app.incidents.models import OperationalIncident
from app.incidents.schemas import AuditEventResponse, AssignmentHistoryResponse, StatusHistoryResponse
from app.main import app
from app.management.audit import ManagementAuditEvent
from app.management.schemas import ManagementAuditEventResponse
from tests.reference_fixtures import reference_ids


@pytest.mark.parametrize("action", ["created", "updated", "activated", "deactivated"])
@pytest.mark.parametrize("resource", ["catalogValue", "clinics", "jurisdictions", "affected-systems", "responsible-areas"])
def test_management_event_allowlists_redact_text_without_mutating_input(resource, action):
    source = {"key": "syntheticKey", "label": "synthetic-private-marker", "is_active": True}
    if resource == "clinics":
        source["jurisdiction_id"] = str(uuid4())
    if resource == "catalogValue":
        source.update(description="synthetic-private-marker", is_open=None, sort_order=1,
                      effective_from="2026-10-31T00:00:00+00:00", effective_to=None)
    original = deepcopy(source)
    result = project_snapshot(resource, action, source)
    assert source == original
    assert result["key"] == source["key"]
    assert result["label"] == REDACTED
    assert result["is_active"] is True
    assert result["_redacted"] is True
    assert "synthetic-private-marker" not in str(result)


@pytest.mark.parametrize(
    ("resource", "action", "source"),
    [
        ("OperationalIncident", "created", {"status_value_id": str(uuid4())}),
        ("OperationalIncident", "status_changed", {"status_value_id": str(uuid4())}),
        ("OperationalIncident", "assigned", {"responsible_area_id": str(uuid4())}),
        ("OperationalIncident", "updated", {"compliance_review_id": "None"}),
        ("affected-systems", "coverageChanged", {"jurisdiction_ids": [str(uuid4()), str(uuid4())]}),
        ("complianceReview", "created", {"jurisdiction_id": str(uuid4()), "status": "open"}),
        ("complianceReview", "statusChanged", {"status": "closed"}),
        ("complianceReview", "associated", {"incident_id": str(uuid4())}),
        ("complianceReview", "disassociated", {"incident_id": str(uuid4())}),
    ],
)
def test_technical_snapshots_preserve_values(resource, action, source):
    assert project_snapshot(resource, action, source) == source


@pytest.mark.parametrize("source", [[], ["synthetic-secret"], "synthetic-secret", 1])
def test_unknown_root_shapes_are_explicitly_withheld(source):
    assert project_snapshot("OperationalIncident", "updated", source) == {"_redacted": True}


def test_invalid_and_nested_fields_do_not_hide_valid_references():
    reference = str(uuid4())
    source = {
        "status_value_id": reference, "password": "synthetic-secret",
        "nested": [{"token": "synthetic-secret"}],
    }
    assert project_snapshot("OperationalIncident", "status_changed", source) == {
        "status_value_id": reference, "_redacted": True,
    }
    assert project_snapshot("affected-systems", "coverageChanged", {
        "jurisdiction_ids": [{"password": "synthetic-secret"}],
    }) == {"_redacted": True}
    assert project_snapshot("unknown", "unknown", source) == {"_redacted": True}
    assert project_snapshot("OperationalIncident", "created", None) is None
    assert project_snapshot("OperationalIncident", "updated", {}) == {}


@pytest.mark.parametrize("model", [StatusHistoryResponse, AssignmentHistoryResponse])
def test_histories_redact_reason_preserving_actor_and_references(model):
    actor = uuid4()
    now = datetime.now(UTC)
    source = SimpleNamespace(
        id=uuid4(), changed_by=actor, changed_at=now, reason="synthetic-private-marker",
        from_status_value_id=None, to_status_value_id=uuid4(),
        from_responsible_area_id=None, to_responsible_area_id=uuid4(),
    )
    result = model.model_validate(source)
    assert result.reason == REDACTED
    assert result.changed_by == actor and result.changed_at == now
    assert source.reason == "synthetic-private-marker"
    source.reason = None
    assert model.model_validate(source).reason is None


@pytest.mark.parametrize("year", [2020, 2026])
def test_incident_audit_uses_same_policy_for_historical_events(year):
    source = SimpleNamespace(
        id=uuid4(), entity_type="OperationalIncident", entity_id=uuid4(), action="updated",
        actor_id=uuid4(), occurred_at=datetime(year, 1, 1, tzinfo=UTC),
        before_data={"description": "synthetic-private-marker", "compliance_review_id": "None"},
        after_data={"description": None, "compliance_review_id": str(uuid4())},
    )
    before = deepcopy(source.before_data)
    result = AuditEventResponse.model_validate(source)
    assert result.before_data == {"description": REDACTED, "compliance_review_id": "None", "_redacted": True}
    assert result.after_data == source.after_data
    assert source.before_data == before
    assert result.actor_id == source.actor_id and result.occurred_at == source.occurred_at
    assert "correlation_id" not in result.model_dump()


@pytest.mark.parametrize("role", ["technology", "responsibleArea", "direction", None])
def test_audit_routes_keep_existing_denials(role):
    async def workflow():
        headers = {} if role is None else {"Authorization": f"Bearer {create_access_token(uuid4(), role, uuid4())}"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            for route in (f"/incidents/{uuid4()}/audit", "/management/audit-events"):
                assert (await client.get(route, headers=headers)).status_code == (401 if role is None else 403)
    asyncio.run(workflow())


@pytest.mark.integration
def test_http_management_projection_preserves_persisted_current_and_historical_events():
    if not os.getenv("DATABASE_URL") or SessionLocal is None:
        pytest.skip("DATABASE_URL is required for integration tests")

    async def workflow():
        resource_id = uuid4()
        refs = await reference_ids()
        async with SessionLocal() as session:
            catalog_ids = dict((await session.execute(select(CatalogValue.key, CatalogValue.id))).all())
            now = datetime.now(UTC)
            actor_id = uuid4()
            incident = OperationalIncident(
                id=uuid4(), incident_identifier=f"SYN-{uuid4().hex}", title="Synthetic incident",
                description="Synthetic description", reporter_id=actor_id,
                clinic_id=refs["dev-us-clinic-01"], jurisdiction_id=refs["US"],
                affected_system_id=refs["usEhr"], responsible_area_id=refs["technology"],
                entry_channel_value_id=catalog_ids["clinicPhone"],
                incident_type_value_id=catalog_ids["systemAvailability"],
                severity_value_id=catalog_ids["critical"], status_value_id=catalog_ids["new"],
                created_at=now, updated_at=now, created_by=actor_id, updated_by=actor_id,
            )
            session.add(incident)
            await session.flush()
            incident_events = [AuditEvent(
                id=uuid4(), entity_type="OperationalIncident", entity_id=incident.id,
                action="updated", actor_id=actor_id, occurred_at=datetime(year, 1, 1, tzinfo=UTC),
                before_data={"description": "synthetic-private-marker", "compliance_review_id": "None"},
                after_data={"description": "synthetic-private-marker", "password": "synthetic-secret"},
            ) for year in (2020, 2026)]
            status_history = IncidentStatusHistory(
                id=uuid4(), incident_id=incident.id, from_status_value_id=None,
                to_status_value_id=catalog_ids["new"], changed_by=actor_id,
                reason="synthetic-private-marker", changed_at=now,
            )
            assignment_history = IncidentAssignmentHistory(
                id=uuid4(), incident_id=incident.id, from_responsible_area_id=None,
                to_responsible_area_id=refs["technology"], changed_by=actor_id,
                reason="synthetic-private-marker", changed_at=now,
            )
            session.add_all([*incident_events, status_history, assignment_history])
            events = [ManagementAuditEvent(
                id=uuid4(), resource_type="catalogValue", resource_id=resource_id,
                action="updated", actor_id=uuid4(), correlation_id=uuid4(),
                occurred_at=datetime(year, 1, 1, tzinfo=UTC), reason="synthetic-private-marker",
                before_data={"key": "synthetic", "description": "synthetic-private-marker"},
                after_data={"key": "synthetic", "description": "synthetic-private-marker", "password": "synthetic-secret"},
            ) for year in (2020, 2026)]
            session.add_all(events)
            await session.flush()
            originals = {event.id: (deepcopy(event.before_data), deepcopy(event.after_data), event.reason) for event in events}
            incident_originals = {event.id: (deepcopy(event.before_data), deepcopy(event.after_data)) for event in incident_events}

            async def isolated_session():
                yield session

            previous = app.dependency_overrides.get(get_session)
            app.dependency_overrides[get_session] = isolated_session
            try:
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    for role in ("admin", "compliance"):
                        response = await client.get(
                            f"/management/audit-events?resource_id={resource_id}",
                            headers={"Authorization": f"Bearer {create_access_token(uuid4(), role)}"},
                        )
                        assert response.status_code == 200
                        assert response.json()["total"] == 2
                        assert "synthetic-private-marker" not in response.text
                        assert "synthetic-secret" not in response.text
                        for item, event in zip(response.json()["items"], reversed(events)):
                            assert item["actor_id"] == str(event.actor_id)
                            assert item["correlation_id"] == str(event.correlation_id)
                            assert item["reason"] == REDACTED
                            assert item["after_data"] == {"key": "synthetic", "description": REDACTED, "_redacted": True}
                        incident_response = await client.get(
                            f"/incidents/{incident.id}/audit",
                            headers={"Authorization": f"Bearer {create_access_token(uuid4(), role)}"},
                        )
                        assert incident_response.status_code == 200
                        assert len(incident_response.json()) == 2
                        assert "synthetic-private-marker" not in incident_response.text
                        assert "synthetic-secret" not in incident_response.text
                        for item, event in zip(incident_response.json(), incident_events):
                            assert item["id"] == str(event.id)
                            assert item["actor_id"] == str(actor_id)
                            assert item["before_data"]["compliance_review_id"] == "None"
                            assert item["after_data"] == {"description": REDACTED, "_redacted": True}
                    for role in ("admin", "compliance", "technology", "responsibleArea"):
                        headers = {"Authorization": f"Bearer {create_access_token(uuid4(), role, refs['technology'])}"}
                        for suffix in ("history", "assignment-history"):
                            history_response = await client.get(f"/incidents/{incident.id}/{suffix}", headers=headers)
                            assert history_response.status_code == 200
                            assert history_response.json()[0]["reason"] == REDACTED
                            assert history_response.json()[0]["changed_by"] == str(actor_id)
                    wrong_area = await client.get(
                        f"/incidents/{incident.id}/history",
                        headers={"Authorization": f"Bearer {create_access_token(uuid4(), 'responsibleArea', refs['clinicalOperations'])}"},
                    )
                    assert wrong_area.status_code == 403
                # Force a fresh SQL read rather than trusting the ORM identity map.
                rows = (await session.execute(select(
                    ManagementAuditEvent.id, ManagementAuditEvent.before_data,
                    ManagementAuditEvent.after_data, ManagementAuditEvent.reason,
                ).where(ManagementAuditEvent.resource_id == resource_id))).all()
                assert {row.id: (row.before_data, row.after_data, row.reason) for row in rows} == originals
                incident_rows = (await session.execute(select(
                    AuditEvent.id, AuditEvent.before_data, AuditEvent.after_data,
                ).where(AuditEvent.entity_id == incident.id))).all()
                assert {row.id: (row.before_data, row.after_data) for row in incident_rows} == incident_originals
                assert await session.scalar(select(IncidentStatusHistory.reason).where(IncidentStatusHistory.id == status_history.id)) == "synthetic-private-marker"
                assert await session.scalar(select(IncidentAssignmentHistory.reason).where(IncidentAssignmentHistory.id == assignment_history.id)) == "synthetic-private-marker"
            finally:
                if previous is None:
                    app.dependency_overrides.pop(get_session, None)
                else:
                    app.dependency_overrides[get_session] = previous
                await session.rollback()
        if engine is not None:
            await engine.dispose()
    asyncio.run(workflow())
