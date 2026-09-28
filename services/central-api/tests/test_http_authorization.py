import asyncio
import os
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.auth.roles import ADMIN, COMPLIANCE, DIRECTION, RESPONSIBLE_AREA, TECHNOLOGY
from app.auth.security import create_access_token
from app.db.models.catalog import Catalog, CatalogValue
from app.db.session import SessionLocal, engine
from app.incidents.history import AuditEvent, IncidentAssignmentHistory, IncidentStatusHistory
from app.incidents.models import OperationalIncident
from app.main import app
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
