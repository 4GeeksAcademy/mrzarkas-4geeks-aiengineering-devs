import asyncio
import os
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.auth.roles import ADMIN, COMPLIANCE, DIRECTION, RESPONSIBLE_AREA, TECHNOLOGY
from app.auth.security import create_access_token
from app.compliance.models import ComplianceReview
from app.db.models.catalog import Catalog, CatalogValue
from app.db.session import SessionLocal, engine
from app.incidents.history import AuditEvent, IncidentAssignmentHistory, IncidentStatusHistory
from app.incidents.models import OperationalIncident
from app.management.audit import ManagementAuditEvent
from app.main import app
from app.reference_data.models import AffectedSystem, Clinic, affected_system_jurisdiction
from tests.reference_fixtures import reference_ids


pytestmark = pytest.mark.integration


async def _catalog_ids() -> dict[str, UUID]:
    assert SessionLocal is not None
    async with SessionLocal() as session:
        result = await session.execute(
            select(CatalogValue.key, CatalogValue.id)
            .join(Catalog)
            .where(Catalog.catalog_name.in_(["entryChannel", "incidentType", "severity"]))
        )
        return {key: value_id for key, value_id in result.all()}


def _bearer(role: str, area_id: UUID | None = None) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(uuid4(), role, area_id)}"}


def test_http_authorization_enforces_area_capability_and_audit_access() -> None:
    if not os.getenv("DATABASE_URL") or SessionLocal is None:
        pytest.skip("DATABASE_URL is required for integration tests")

    async def workflow() -> None:
        ids = await _catalog_ids()
        refs = await reference_ids()
        required = {"clinicPhone", "systemAvailability", "critical"}
        if not required.issubset(ids):
            pytest.skip("Catalog seed is required for integration tests")

        own_area_id = refs["technology"]
        other_area_id = refs["clinicalOperations"]
        incident_id: UUID | None = None
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            base_payload = {
                "title": "Reference validation test",
                "description": "Verifies US and UK reference compatibility.",
                "reporter_id": str(uuid4()),
                "clinic_id": str(refs["dev-us-clinic-01"]),
                "jurisdiction_id": str(refs["US"]),
                "affected_system_id": str(refs["usEhr"]),
                "entry_channel_value_id": str(ids["clinicPhone"]),
                "incident_type_value_id": str(ids["systemAvailability"]),
                "severity_value_id": str(ids["critical"]),
                "responsible_area_id": str(own_area_id),
            }
            invalid_clinic_jurisdiction = await client.post(
                "/incidents",
                headers=_bearer(ADMIN),
                json={**base_payload, "jurisdiction_id": str(refs["UK"]), "affected_system_id": str(refs["ukEhr"])},
            )
            assert invalid_clinic_jurisdiction.status_code == 422

            invalid_system_jurisdiction = await client.post(
                "/incidents",
                headers=_bearer(ADMIN),
                json={**base_payload, "affected_system_id": str(refs["ukEhr"])},
            )
            assert invalid_system_jurisdiction.status_code == 422

            created = await client.post(
                "/incidents",
                headers=_bearer(ADMIN),
                json={**base_payload, "title": "HTTP authorization test"},
            )
            assert created.status_code == 201
            incident_id = UUID(created.json()["id"])

            direction_list = await client.get("/incidents", headers=_bearer(DIRECTION))
            assert direction_list.status_code == 200
            direction_item = next(
                item for item in direction_list.json()["items"] if item["id"] == str(incident_id)
            )
            assert {"description", "reporter_id", "compliance_review_id", "created_by", "updated_by"}.isdisjoint(direction_item)

            direction_detail = await client.get(
                f"/incidents/{incident_id}", headers=_bearer(DIRECTION)
            )
            assert direction_detail.status_code == 403

            own_area_read = await client.get(
                f"/incidents/{incident_id}",
                headers=_bearer(RESPONSIBLE_AREA, own_area_id),
            )
            assert own_area_read.status_code == 200

            other_area_read = await client.get(
                f"/incidents/{incident_id}",
                headers=_bearer(RESPONSIBLE_AREA, other_area_id),
            )
            assert other_area_read.status_code == 403

            area_audit = await client.get(
                f"/incidents/{incident_id}/audit",
                headers=_bearer(RESPONSIBLE_AREA, own_area_id),
            )
            assert area_audit.status_code == 403

            compliance_audit = await client.get(
                f"/incidents/{incident_id}/audit",
                headers=_bearer(COMPLIANCE),
            )
            assert compliance_audit.status_code == 200
            assert {event["action"] for event in compliance_audit.json()} == {"created"}

            denied_assignment = await client.post(
                f"/incidents/{incident_id}/assignments",
                headers=_bearer(TECHNOLOGY),
                json={"responsible_area_id": str(other_area_id)},
            )
            assert denied_assignment.status_code == 403

        assert incident_id is not None
        async with SessionLocal() as session:
            await session.execute(delete(AuditEvent).where(AuditEvent.entity_id == incident_id))
            await session.execute(
                delete(IncidentAssignmentHistory).where(
                    IncidentAssignmentHistory.incident_id == incident_id
                )
            )
            await session.execute(
                delete(IncidentStatusHistory).where(
                    IncidentStatusHistory.incident_id == incident_id
                )
            )
            await session.execute(delete(OperationalIncident).where(OperationalIncident.id == incident_id))
            await session.commit()

        if engine is not None:
            await engine.dispose()

    asyncio.run(workflow())


def test_management_routes_enforce_provisional_capabilities() -> None:
    if not os.getenv("DATABASE_URL") or SessionLocal is None:
        pytest.skip("DATABASE_URL is required for integration tests")

    async def workflow() -> None:
        refs = await reference_ids()
        if "US" not in refs:
            pytest.skip("Reference seed is required for integration tests")

        review_id: UUID | None = None
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            assert (await client.get("/catalogs/severity", headers=_bearer(DIRECTION))).status_code == 403
            assert (await client.get("/catalogs/severity", headers=_bearer(TECHNOLOGY))).status_code == 200

            payload = {"jurisdiction_id": str(refs["US"]), "status": "open"}
            assert (await client.post("/compliance-reviews", headers=_bearer(TECHNOLOGY), json=payload)).status_code == 403
            assert (await client.post("/compliance-reviews", headers=_bearer(DIRECTION), json=payload)).status_code == 403

            created = await client.post(
                "/compliance-reviews", headers=_bearer(COMPLIANCE), json=payload
            )
            assert created.status_code == 201
            review_id = UUID(created.json()["id"])

            assert (await client.get(f"/compliance-reviews/{review_id}", headers=_bearer(COMPLIANCE))).status_code == 200
            assert (await client.get(f"/compliance-reviews/{review_id}", headers=_bearer(ADMIN))).status_code == 200
            assert (await client.get(f"/compliance-reviews/{review_id}", headers=_bearer(TECHNOLOGY))).status_code == 403

        assert review_id is not None
        async with SessionLocal() as session:
            await session.execute(
                delete(ManagementAuditEvent).where(
                    ManagementAuditEvent.resource_id == review_id
                )
            )
            await session.execute(delete(ComplianceReview).where(ComplianceReview.id == review_id))
            await session.commit()
        if engine is not None:
            await engine.dispose()

    asyncio.run(workflow())


def test_admin_manages_catalog_values_with_audit_and_no_physical_delete() -> None:
    if not os.getenv("DATABASE_URL") or SessionLocal is None:
        pytest.skip("DATABASE_URL is required for integration tests")

    async def workflow() -> None:
        created_id: UUID | None = None
        original_catalog: tuple[int, object, UUID] | None = None
        async with SessionLocal() as session:
            original_catalog = (
                await session.execute(
                    select(Catalog.version, Catalog.updated_at, Catalog.updated_by).where(
                        Catalog.catalog_name == "severity"
                    )
                )
            ).one_or_none()
        if original_catalog is None:
            pytest.skip("Catalog seed is required for integration tests")

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            assert (await client.get("/management/catalogs", headers=_bearer(DIRECTION))).status_code == 403
            assert (await client.post("/management/catalogs/severity/values", headers=_bearer(TECHNOLOGY), json={})).status_code == 403

            payload = {
                "key": "m3Synthetic",
                "label": "M3 Synthetic",
                "description": "Synthetic configuration value for integration tests.",
                "sort_order": 99,
                "effective_from": "2026-01-01T00:00:00Z",
            }
            created = await client.post(
                "/management/catalogs/severity/values", headers=_bearer(ADMIN), json=payload
            )
            assert created.status_code == 201
            created_id = UUID(created.json()["id"])
            assert created.json()["key"] == "m3Synthetic"

            duplicate = await client.post(
                "/management/catalogs/severity/values", headers=_bearer(ADMIN), json=payload
            )
            assert duplicate.status_code == 409

            immutable_key = await client.patch(
                f"/management/catalogs/severity/values/{created_id}",
                headers=_bearer(ADMIN),
                json={"key": "cannotChange"},
            )
            assert immutable_key.status_code == 422

            updated = await client.patch(
                f"/management/catalogs/severity/values/{created_id}",
                headers=_bearer(ADMIN),
                json={"label": "M3 Synthetic Updated", "sort_order": 98},
            )
            assert updated.status_code == 200
            assert updated.json()["label"] == "M3 Synthetic Updated"

            missing_reason = await client.post(
                f"/management/catalogs/severity/values/{created_id}/activation",
                headers=_bearer(ADMIN),
                json={"is_active": False},
            )
            assert missing_reason.status_code == 422
            deactivated = await client.post(
                f"/management/catalogs/severity/values/{created_id}/activation",
                headers=_bearer(ADMIN),
                json={"is_active": False, "reason": "Synthetic lifecycle test"},
            )
            assert deactivated.status_code == 200
            assert deactivated.json()["is_active"] is False

            public_values = await client.get("/catalogs/severity", headers=_bearer(ADMIN))
            assert public_values.status_code == 200
            assert "m3Synthetic" not in {item["key"] for item in public_values.json()["values"]}
            managed_values = await client.get(
                "/management/catalogs/severity/values", headers=_bearer(ADMIN)
            )
            assert any(item["id"] == str(created_id) and not item["is_active"] for item in managed_values.json()["items"])

        assert created_id is not None
        async with SessionLocal() as session:
            events = (
                await session.execute(
                    select(ManagementAuditEvent.action).where(
                        ManagementAuditEvent.resource_type == "catalogValue",
                        ManagementAuditEvent.resource_id == created_id,
                    ).order_by(ManagementAuditEvent.occurred_at)
                )
            ).scalars().all()
            assert events == ["created", "updated", "deactivated"]
            await session.execute(delete(ManagementAuditEvent).where(ManagementAuditEvent.resource_id == created_id))
            await session.execute(delete(CatalogValue).where(CatalogValue.id == created_id))
            await session.execute(
                Catalog.__table__.update()
                .where(Catalog.catalog_name == "severity")
                .values(
                    version=original_catalog[0],
                    updated_at=original_catalog[1],
                    updated_by=original_catalog[2],
                )
            )
            await session.commit()
        if engine is not None:
            await engine.dispose()

    asyncio.run(workflow())


def test_admin_manages_reference_data_without_invalidating_history() -> None:
    if not os.getenv("DATABASE_URL") or SessionLocal is None:
        pytest.skip("DATABASE_URL is required for integration tests")

    async def workflow() -> None:
        ids = await _catalog_ids()
        refs = await reference_ids()
        required = {"clinicPhone", "systemAvailability", "critical"}
        if not required.issubset(ids) or not {"US", "UK", "technology"}.issubset(refs):
            pytest.skip("Synthetic seeds are required for integration tests")

        clinic_id: UUID | None = None
        system_id: UUID | None = None
        incident_id: UUID | None = None
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            assert (await client.get("/management/reference-data/clinics", headers=_bearer(DIRECTION))).status_code == 403
            listed = await client.get("/management/reference-data/clinics", headers=_bearer(TECHNOLOGY))
            assert listed.status_code == 200

            clinic = await client.post(
                "/management/reference-data/clinics",
                headers=_bearer(ADMIN),
                json={"key": "m4-synthetic-clinic", "label": "M4 Synthetic Clinic", "jurisdiction_id": str(refs["US"])},
            )
            assert clinic.status_code == 201
            clinic_id = UUID(clinic.json()["id"])
            assert clinic.json()["jurisdiction_id"] == str(refs["US"])

            system = await client.post(
                "/management/reference-data/affected-systems",
                headers=_bearer(ADMIN),
                json={"key": "m4SyntheticSystem", "label": "M4 Synthetic System"},
            )
            assert system.status_code == 201
            system_id = UUID(system.json()["id"])
            coverage = await client.put(
                f"/management/affected-systems/{system_id}/jurisdictions",
                headers=_bearer(ADMIN),
                json={"jurisdiction_ids": [str(refs["US"])]},
            )
            assert coverage.status_code == 200

            incident_payload = {
                "title": "M4 compatibility incident",
                "description": "Uses only synthetic reference data.",
                "reporter_id": str(uuid4()),
                "clinic_id": str(clinic_id),
                "jurisdiction_id": str(refs["US"]),
                "affected_system_id": str(system_id),
                "entry_channel_value_id": str(ids["clinicPhone"]),
                "incident_type_value_id": str(ids["systemAvailability"]),
                "severity_value_id": str(ids["critical"]),
                "responsible_area_id": str(refs["technology"]),
            }
            created = await client.post("/incidents", headers=_bearer(ADMIN), json=incident_payload)
            assert created.status_code == 201
            incident_id = UUID(created.json()["id"])

            clinic_change = await client.patch(
                f"/management/reference-data/clinics/{clinic_id}",
                headers=_bearer(ADMIN),
                json={"jurisdiction_id": str(refs["UK"])},
            )
            assert clinic_change.status_code == 409
            coverage_removal = await client.put(
                f"/management/affected-systems/{system_id}/jurisdictions",
                headers=_bearer(ADMIN),
                json={"jurisdiction_ids": []},
            )
            assert coverage_removal.status_code == 409

            deactivated = await client.post(
                f"/management/reference-data/clinics/{clinic_id}/activation",
                headers=_bearer(ADMIN),
                json={"is_active": False, "reason": "Synthetic lifecycle test"},
            )
            assert deactivated.status_code == 200
            assert deactivated.json()["is_active"] is False
            rejected_inactive = await client.post(
                "/incidents", headers=_bearer(ADMIN), json=incident_payload
            )
            assert rejected_inactive.status_code == 422

        assert clinic_id is not None and system_id is not None and incident_id is not None
        async with SessionLocal() as session:
            await session.execute(delete(AuditEvent).where(AuditEvent.entity_id == incident_id))
            await session.execute(delete(IncidentStatusHistory).where(IncidentStatusHistory.incident_id == incident_id))
            await session.execute(delete(OperationalIncident).where(OperationalIncident.id == incident_id))
            await session.execute(delete(ManagementAuditEvent).where(ManagementAuditEvent.resource_id.in_([clinic_id, system_id])))
            await session.execute(affected_system_jurisdiction.delete().where(affected_system_jurisdiction.c.affected_system_id == system_id))
            await session.execute(delete(Clinic).where(Clinic.id == clinic_id))
            await session.execute(delete(AffectedSystem).where(AffectedSystem.id == system_id))
            await session.commit()
        if engine is not None:
            await engine.dispose()

    asyncio.run(workflow())


def test_compliance_review_lifecycle_and_jurisdiction_association_are_audited() -> None:
    if not os.getenv("DATABASE_URL") or SessionLocal is None:
        pytest.skip("DATABASE_URL is required for integration tests")

    async def workflow() -> None:
        ids = await _catalog_ids()
        refs = await reference_ids()
        if not {"clinicPhone", "systemAvailability", "critical"}.issubset(ids) or not {"US", "UK", "dev-us-clinic-01", "usEhr", "technology"}.issubset(refs):
            pytest.skip("Synthetic seeds are required for integration tests")

        us_review_id: UUID | None = None
        uk_review_id: UUID | None = None
        incident_id: UUID | None = None
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            us_review = await client.post(
                "/compliance-reviews",
                headers=_bearer(COMPLIANCE),
                json={"jurisdiction_id": str(refs["US"]), "status": "open"},
            )
            assert us_review.status_code == 201
            us_review_id = UUID(us_review.json()["id"])
            uk_review = await client.post(
                "/compliance-reviews",
                headers=_bearer(COMPLIANCE),
                json={"jurisdiction_id": str(refs["UK"]), "status": "open"},
            )
            assert uk_review.status_code == 201
            uk_review_id = UUID(uk_review.json()["id"])

            denied_status_change = await client.patch(
                f"/compliance-reviews/{us_review_id}/status",
                headers=_bearer(TECHNOLOGY),
                json={"status": "inReview"},
            )
            assert denied_status_change.status_code == 403
            in_review = await client.patch(
                f"/compliance-reviews/{us_review_id}/status",
                headers=_bearer(COMPLIANCE),
                json={"status": "inReview"},
            )
            assert in_review.status_code == 200
            assert in_review.json()["status"] == "inReview"
            missing_close_reason = await client.patch(
                f"/compliance-reviews/{us_review_id}/status",
                headers=_bearer(COMPLIANCE),
                json={"status": "closed"},
            )
            assert missing_close_reason.status_code == 422

            base_payload = {
                "title": "M5 review association incident",
                "description": "Uses a synthetic ComplianceReview.",
                "reporter_id": str(uuid4()),
                "clinic_id": str(refs["dev-us-clinic-01"]),
                "jurisdiction_id": str(refs["US"]),
                "affected_system_id": str(refs["usEhr"]),
                "entry_channel_value_id": str(ids["clinicPhone"]),
                "incident_type_value_id": str(ids["systemAvailability"]),
                "severity_value_id": str(ids["critical"]),
                "responsible_area_id": str(refs["technology"]),
            }
            wrong_jurisdiction = await client.post(
                "/incidents",
                headers=_bearer(ADMIN),
                json={**base_payload, "compliance_review_id": str(uk_review_id)},
            )
            assert wrong_jurisdiction.status_code == 422
            associated = await client.post(
                "/incidents",
                headers=_bearer(ADMIN),
                json={**base_payload, "compliance_review_id": str(us_review_id)},
            )
            assert associated.status_code == 201
            incident_id = UUID(associated.json()["id"])

            closed = await client.patch(
                f"/compliance-reviews/{us_review_id}/status",
                headers=_bearer(COMPLIANCE),
                json={"status": "closed", "reason": "Synthetic review completed"},
            )
            assert closed.status_code == 200
            assert closed.json()["status"] == "closed"
            assert (await client.get(f"/compliance-reviews/{us_review_id}", headers=_bearer(COMPLIANCE))).status_code == 200
            assert (await client.get(f"/compliance-reviews/{us_review_id}", headers=_bearer(TECHNOLOGY))).status_code == 403

        assert us_review_id is not None and uk_review_id is not None and incident_id is not None
        async with SessionLocal() as session:
            actions = (
                await session.execute(
                    select(ManagementAuditEvent.action)
                    .where(
                        ManagementAuditEvent.resource_type == "complianceReview",
                        ManagementAuditEvent.resource_id == us_review_id,
                    )
                    .order_by(ManagementAuditEvent.occurred_at)
                )
            ).scalars().all()
            assert actions == ["created", "statusChanged", "associated", "statusChanged"]
            await session.execute(delete(AuditEvent).where(AuditEvent.entity_id == incident_id))
            await session.execute(delete(IncidentStatusHistory).where(IncidentStatusHistory.incident_id == incident_id))
            await session.execute(delete(OperationalIncident).where(OperationalIncident.id == incident_id))
            await session.execute(ManagementAuditEvent.__table__.delete().where(ManagementAuditEvent.resource_id.in_([us_review_id, uk_review_id])))
            await session.execute(ComplianceReview.__table__.delete().where(ComplianceReview.id.in_([us_review_id, uk_review_id])))
            await session.commit()
        if engine is not None:
            await engine.dispose()

    asyncio.run(workflow())


def test_management_audit_endpoint_is_restricted_and_filterable() -> None:
    if not os.getenv("DATABASE_URL") or SessionLocal is None:
        pytest.skip("DATABASE_URL is required for integration tests")

    async def workflow() -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            denied = await client.get("/management/audit-events", headers=_bearer(TECHNOLOGY))
            assert denied.status_code == 403
            allowed = await client.get(
                "/management/audit-events?resource_type=complianceReview&limit=1",
                headers=_bearer(COMPLIANCE),
            )
            assert allowed.status_code == 200
            assert set(allowed.json()) == {"items", "total"}
        if engine is not None:
            await engine.dispose()

    asyncio.run(workflow())
