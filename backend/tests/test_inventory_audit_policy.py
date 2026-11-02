"""Approval HC-INV-APPROVAL-2026-11-02: synthetic historical and denial evidence."""
import asyncio
from datetime import UTC, datetime, timedelta, timezone
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, func, text, event
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.auth.dependencies import Actor
from app.auth.security import create_access_token
from app.db.session import get_session
from app.inventory import service as svc
from app.inventory.models import InventoryAccessDenial, InventoryAudit, InventoryItem, InventoryMovement
from app.inventory.retention import retention_deadline, RETENTION_MONTHS
from app.inventory.schemas import ItemCreate, ClinicConfig, MovementCreate
from app.main import app
from app.reference_data.models import Clinic
from test_inventory import isolated_url, setup_fixture


def test_retention_is_24_calendar_months_in_utc():
    assert RETENTION_MONTHS == 24
    assert retention_deadline(datetime(2024, 2, 29, 11, tzinfo=UTC)) == datetime(2026, 2, 28, 11, tzinfo=UTC)
    assert retention_deadline(datetime(2026, 11, 2, 11, tzinfo=UTC)) == datetime(2028, 11, 2, 11, tzinfo=UTC)
    assert retention_deadline(datetime(2026, 11, 2, 11, tzinfo=timezone(timedelta(hours=2)))) == datetime(2028, 11, 2, 9, tzinfo=UTC)
    with pytest.raises(ValueError):
        retention_deadline(datetime(2026, 11, 2))


@pytest.mark.integration
def test_historical_country_controls_reads_after_clinic_country_changes():
    async def run():
        engine = create_async_engine(isolated_url())
        async with engine.connect() as connection:
            outer = await connection.begin()
            factory = async_sessionmaker(connection, expire_on_commit=False, join_transaction_mode="create_savepoint")
            async with factory() as session, session.begin():
                c1, c2, admin, manager, region = await setup_fixture(session)
                original_country = c1.jurisdiction_id
                value = await svc.create_item(session, admin, ItemCreate(title="Synthetic historical", product_code="HIST-" + str(uuid4()), unit="piece"))
                await svc.configure(session, manager, value.id, c1.id, ClinicConfig(reorder_point=5))
                before_move = await svc.movement(session, manager, MovementCreate(item_id=value.id, clinic_id=c1.id, kind="in", quantity=10))
            async with factory() as session, session.begin():
                clinic = await session.get(Clinic, c1.id)
                clinic.jurisdiction_id = c2.jurisdiction_id
            async with factory() as session, session.begin():
                after_move = await svc.movement(session, manager, MovementCreate(item_id=value.id, clinic_id=c1.id, kind="out", quantity=1))
                assert before_move.jurisdiction_id == original_country
                assert after_move.jurisdiction_id == c2.jurisdiction_id
                assert before_move.jurisdiction_key != after_move.jurisdiction_key
            async def override():
                async with factory() as session:
                    yield session
            app.dependency_overrides[get_session] = override
            try:
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    def headers(actor):
                        return {"Authorization": "Bearer " + create_access_token(actor.id, actor.role, clinic_ids=actor.clinic_ids, jurisdiction_ids=actor.jurisdiction_ids)}
                    old_auditor = Actor(uuid4(), "inventoryAuditor", jurisdiction_ids=(original_country,))
                    new_auditor = Actor(uuid4(), "inventoryAuditor", jurisdiction_ids=(c2.jurisdiction_id,))
                    base = f"/inventory/items/{value.id}"
                    for actor, expected in ((region, before_move), (old_auditor, before_move), (new_auditor, after_move)):
                        response = await client.get(base + "/movements", params={"clinic_id": str(c1.id)}, headers=headers(actor))
                        assert response.status_code == 200, response.text
                        records = response.json()
                        assert [row["id"] for row in records] == [str(expected.id)]
                        assert records[0]["jurisdiction_id"] == str(expected.jurisdiction_id)
                        assert records[0]["result"] == "accepted"
                        assert records[0]["resulting_quantity"] == expected.previous_quantity + expected.delta
                        assert records[0]["retention_until"] == retention_deadline(expected.occurred_at).isoformat().replace("+00:00", "Z")
                    audit = await client.get(base + "/audit", params={"clinic_id": str(c1.id)}, headers=headers(old_auditor))
                    assert audit.status_code == 200
                    clinical = [row for row in audit.json() if row["clinic_id"] is not None]
                    assert clinical and all(row["jurisdiction_id"] == str(original_country) for row in clinical)
                    # Historical authorization does not grant current stock access.
                    denied = await client.get(base + "/stock", params={"clinic_id": str(c1.id)}, headers=headers(region))
                    assert denied.status_code == 403
                    denials = await client.get("/inventory/access-denials", headers=headers(new_auditor))
                    assert denials.status_code == 200
                    assert any(row["clinic_id"] == str(c1.id) and row["reason_code"] == "scope" for row in denials.json())
            finally:
                app.dependency_overrides.pop(get_session, None)
                await outer.rollback()
        await engine.dispose()
    asyncio.run(run())


@pytest.mark.integration
def test_denials_commit_without_business_changes_and_keep_no_request_text():
    async def run():
        engine = create_async_engine(isolated_url())
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session, session.begin():
            c1, c2, admin, manager, region = await setup_fixture(session)
            value = await svc.create_item(session, admin, ItemCreate(title="Synthetic denial", product_code="DENIAL-" + str(uuid4()), unit="piece"))
            await svc.configure(session, manager, value.id, c1.id, ClinicConfig(reorder_point=5))
        async def override():
            async with factory() as session:
                yield session
        app.dependency_overrides[get_session] = override
        auditor = Actor(uuid4(), "inventoryAuditor", jurisdiction_ids=region.jurisdiction_ids)
        token = create_access_token(auditor.id, auditor.role, jurisdiction_ids=auditor.jurisdiction_ids)
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                payload = dict(item_id=str(value.id), clinic_id=str(c1.id), kind="in", quantity=1, reason="Synthetic text excluded from security evidence")
                response = await client.post("/inventory/movements", headers={"Authorization": "Bearer " + token}, json=payload)
                assert response.status_code == 403, response.text
                async with factory() as session:
                    rows = (await session.scalars(select(InventoryAccessDenial).where(InventoryAccessDenial.actor_id == auditor.id))).all()
                    assert len(rows) == 1
                    denial = rows[0]
                    assert denial.jurisdiction_id == c1.jurisdiction_id and denial.clinic_id == c1.id
                    assert denial.operation == "movement" and denial.reason_code == "permission" and denial.result == "denied"
                    assert "Synthetic text excluded" not in str(denial.__dict__) and token not in str(denial.__dict__)
                    assert await svc.quantity(session, value.id, c1.id) == 0
                    assert await session.scalar(select(func.count()).select_from(InventoryMovement).where(InventoryMovement.item_id == value.id)) == 0
                response = await client.get("/inventory/access-denials", headers={"Authorization": "Bearer " + token})
                assert response.status_code == 200
                assert any(row["id"] == str(denial.id) for row in response.json())
                foreign = Actor(uuid4(), "inventoryAuditor", jurisdiction_ids=(c2.jurisdiction_id,))
                response = await client.get("/inventory/access-denials", headers={"Authorization": "Bearer " + create_access_token(foreign.id, foreign.role, jurisdiction_ids=foreign.jurisdiction_ids)})
                assert response.status_code == 200 and all(row["id"] != str(denial.id) for row in response.json())
                # Invalid references cannot manufacture a country or retain arbitrary identifiers.
                unknown = str(uuid4())
                await client.post("/inventory/movements", headers={"Authorization": "Bearer " + token}, json={**payload, "clinic_id": unknown})
                async with factory() as session:
                    last = (await session.scalars(select(InventoryAccessDenial).where(InventoryAccessDenial.actor_id == auditor.id).order_by(InventoryAccessDenial.occurred_at.desc()))).first()
                    assert last.clinic_id is None and last.jurisdiction_id is None
                # Missing authentication is not recorded as a fabricated actor.
                async with factory() as session:
                    count_before = await session.scalar(select(func.count()).select_from(InventoryAccessDenial))
                assert (await client.get("/inventory/items")).status_code == 401
                async with factory() as session:
                    assert await session.scalar(select(func.count()).select_from(InventoryAccessDenial)) == count_before
                # Mandatory denial evidence fails visibly; access is never granted.
                def fail_denial(session, *args):
                    if any(isinstance(obj, InventoryAccessDenial) for obj in session.new):
                        raise RuntimeError("Synthetic audit unavailability")
                event.listen(Session, "before_flush", fail_denial)
                try:
                    response = await client.post("/inventory/movements", headers={"Authorization": "Bearer " + token}, json=payload)
                    assert response.status_code == 503
                finally:
                    event.remove(Session, "before_flush", fail_denial)
                async with factory() as session:
                    assert await svc.quantity(session, value.id, c1.id) == 0
                    await session.rollback()
                    with pytest.raises(Exception, match="append-only"):
                        async with session.begin():
                            await session.execute(text("DELETE FROM inventory_access_denial WHERE id=:id"), {"id": denial.id})
        finally:
            app.dependency_overrides.pop(get_session, None)
            await engine.dispose()
    asyncio.run(run())
