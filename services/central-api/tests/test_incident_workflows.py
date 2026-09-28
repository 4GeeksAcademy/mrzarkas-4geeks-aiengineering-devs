import asyncio
import os
from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete, select

from app.auth.dependencies import Actor
from app.auth.roles import ADMIN, RESPONSIBLE_AREA
from app.db.models.catalog import Catalog, CatalogValue
from app.db.session import SessionLocal, engine
from app.incidents.history import AuditEvent, IncidentStatusHistory
from app.incidents.router import create_incident, incident_audit, incident_history, transition_incident, update_incident
from app.incidents.schemas import IncidentCreate, IncidentUpdate, StatusTransitionRequest
from app.incidents.models import OperationalIncident


pytestmark = pytest.mark.integration


def _run(coro):
    return asyncio.run(coro)


async def _catalog_ids() -> dict[str, UUID]:
    if SessionLocal is None:
        return {}
    async with SessionLocal() as session:
        result = await session.execute(
            select(CatalogValue.key, CatalogValue.id)
            .join(Catalog)
            .where(
                Catalog.catalog_name.in_(
                    ["entryChannel", "incidentType", "severity", "incidentStatus"]
                )
            )
        )
        return {key: value_id for key, value_id in result.all()}


def test_incident_update_transition_history_and_audit():
    if not os.getenv("DATABASE_URL") or SessionLocal is None:
        pytest.skip("DATABASE_URL is required for integration tests")

    incident_id = None

    async def workflow():
        nonlocal incident_id
        async with SessionLocal() as session:
            ids = await _catalog_ids()
            required = {"clinicPhone", "systemAvailability", "critical", "new", "underAnalysis"}
            if not ids or not required.issubset(ids):
                pytest.skip("Catalog seed is required for integration tests")

            area_id = uuid4()
            admin_actor = Actor(id=uuid4(), role=ADMIN)

            payload = IncidentCreate(
                title="Integration test incident",
                description="Incident workflow integration test",
                reporter_id=uuid4(),
                clinic_id=uuid4(),
                jurisdiction_id=uuid4(),
                affected_system_id=uuid4(),
                entry_channel_value_id=ids["clinicPhone"],
                incident_type_value_id=ids["systemAvailability"],
                severity_value_id=ids["critical"],
                responsible_area_id=area_id,
            )
            incident = await create_incident(payload, session, admin_actor)
            incident_id = incident.id

            updated = await update_incident(
                incident.id,
                IncidentUpdate(title="Updated integration incident"),
                session,
                admin_actor,
            )
            assert updated.title == "Updated integration incident"

            transitioned = await transition_incident(
                incident.id,
                StatusTransitionRequest(
                    status_value_id=ids["underAnalysis"],
                    reason="Begin analysis",
                ),
                session,
                admin_actor,
            )
            assert transitioned.status_value_id == ids["underAnalysis"]

            history = await incident_history(incident.id, session, admin_actor)
            audit = await incident_audit(incident.id, session, admin_actor)
            assert len(history) == 2
            assert history[-1].to_status_value_id == ids["underAnalysis"]
            assert {event.action for event in audit} == {"created", "updated", "status_changed"}

            await session.execute(delete(AuditEvent).where(AuditEvent.entity_id == incident.id))
            await session.execute(delete(IncidentStatusHistory).where(IncidentStatusHistory.incident_id == incident.id))
            await session.execute(delete(OperationalIncident).where(OperationalIncident.id == incident.id))
            await session.commit()

        if engine is not None:
            await engine.dispose()

    _run(workflow())


def test_invalid_transition_is_rejected():
    if not os.getenv("DATABASE_URL") or SessionLocal is None:
        pytest.skip("DATABASE_URL is required for integration tests")

    async def workflow():
        async with SessionLocal() as session:
            ids = await _catalog_ids()
            if not ids or not {"clinicPhone", "systemAvailability", "critical", "new", "closed"}.issubset(ids):
                pytest.skip("Catalog seed is required for integration tests")

            admin_actor = Actor(id=uuid4(), role=ADMIN)

            payload = IncidentCreate(
                title="Invalid transition test",
                description="Transition validation integration test",
                reporter_id=uuid4(), clinic_id=uuid4(), jurisdiction_id=uuid4(),
                affected_system_id=uuid4(), entry_channel_value_id=ids["clinicPhone"],
                incident_type_value_id=ids["systemAvailability"], severity_value_id=ids["critical"],
                responsible_area_id=uuid4(),
            )
            incident = await create_incident(payload, session, admin_actor)
            created_incident_id = incident.id
            with pytest.raises(Exception) as error:
                await transition_incident(
                    created_incident_id,
                    StatusTransitionRequest(status_value_id=ids["closed"]),
                    session,
                    admin_actor,
                )
            assert getattr(error.value, "status_code", None) == 409
            await session.rollback()
            await session.execute(delete(AuditEvent).where(AuditEvent.entity_id == created_incident_id))
            await session.execute(delete(IncidentStatusHistory).where(IncidentStatusHistory.incident_id == created_incident_id))
            await session.execute(delete(OperationalIncident).where(OperationalIncident.id == created_incident_id))
            await session.commit()

        if engine is not None:
            await engine.dispose()

    _run(workflow())


def test_responsible_area_actor_is_limited_to_own_area_create_and_close():
    if not os.getenv("DATABASE_URL") or SessionLocal is None:
        pytest.skip("DATABASE_URL is required for integration tests")

    async def workflow():
        async with SessionLocal() as session:
            ids = await _catalog_ids()
            if not ids or not {"clinicPhone", "systemAvailability", "critical", "new", "cancelled"}.issubset(ids):
                pytest.skip("Catalog seed is required for integration tests")

            own_area_id = uuid4()
            other_area_id = uuid4()
            area_actor = Actor(id=uuid4(), role=RESPONSIBLE_AREA, area_id=own_area_id)

            payload = IncidentCreate(
                title="Area scoped incident",
                description="Created by a responsibleArea actor",
                reporter_id=uuid4(), clinic_id=uuid4(), jurisdiction_id=uuid4(),
                affected_system_id=uuid4(), entry_channel_value_id=ids["clinicPhone"],
                incident_type_value_id=ids["systemAvailability"], severity_value_id=ids["critical"],
                responsible_area_id=own_area_id,
            )
            incident = await create_incident(payload, session, area_actor)

            with pytest.raises(Exception) as create_error:
                await create_incident(
                    payload.model_copy(update={"responsible_area_id": other_area_id}),
                    session,
                    area_actor,
                )
            assert getattr(create_error.value, "status_code", None) == 403

            with pytest.raises(Exception) as update_error:
                await update_incident(
                    incident.id,
                    IncidentUpdate(title="Attempted update"),
                    session,
                    area_actor,
                )
            assert getattr(update_error.value, "status_code", None) == 403

            closed = await transition_incident(
                incident.id,
                StatusTransitionRequest(status_value_id=ids["cancelled"]),
                session,
                area_actor,
            )
            assert closed.status_value_id == ids["cancelled"]

            await session.execute(delete(AuditEvent).where(AuditEvent.entity_id == incident.id))
            await session.execute(delete(IncidentStatusHistory).where(IncidentStatusHistory.incident_id == incident.id))
            await session.execute(delete(OperationalIncident).where(OperationalIncident.id == incident.id))
            await session.commit()

        if engine is not None:
            await engine.dispose()

    _run(workflow())
