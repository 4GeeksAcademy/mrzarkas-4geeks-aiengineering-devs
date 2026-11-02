"""Synthetic inventory tests. Integration runs only on explicitly isolated databases."""
import asyncio
import os
from datetime import UTC, datetime
from uuid import uuid4
from urllib.parse import urlparse
import pytest
from fastapi import HTTPException
from httpx import AsyncClient, ASGITransport
from pydantic import ValidationError
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.auth.dependencies import Actor
from app.auth.security import create_access_token, decode_access_token
from app.inventory import service as svc
from app.inventory.models import InventoryItem, InventoryMovement
from app.inventory.policies import allow, scope, PERMISSIONS
from app.inventory.schemas import ItemCreate, ItemUpdate, MovementCreate, ClinicConfig, LotCreate
from app.reference_data.models import Clinic, Jurisdiction
from app.main import app
from app.db.session import get_session


@pytest.mark.parametrize("field,value", [("stock", 4), ("quantity", 4), ("reorder_point", 5)])
def test_item_rejects_balance_inputs(field, value):
    with pytest.raises(ValidationError):
        ItemCreate(title="Synthetic gauze", product_code="SYN-1", unit="piece", **{field: value})


@pytest.mark.parametrize("quantity", [-1, 0, 1.5, True, "4"])
def test_only_positive_integer_movements(quantity):
    with pytest.raises(ValidationError):
        MovementCreate(item_id=uuid4(), clinic_id=uuid4(), kind="in", quantity=quantity)


def test_count_semantics_and_item_update():
    ids = dict(item_id=uuid4(), clinic_id=uuid4(), kind="adjust")
    assert MovementCreate(**ids, counted_quantity=0, reason="Synthetic recount").counted_quantity == 0
    for kwargs in ({"counted_quantity": 2}, {"counted_quantity": 2, "quantity": 1, "reason": "Synthetic"}, {"counted_quantity": 2, "reason": "Synthetic", "unit": "pack"}):
        with pytest.raises(ValidationError):
            MovementCreate(**ids, **kwargs)
    with pytest.raises(ValidationError):
        ItemUpdate(title=None)
    with pytest.raises(ValidationError):
        ClinicConfig(reorder_point=0)
    assert "stock" not in InventoryItem.__table__.columns


@pytest.mark.parametrize("role", ["admin", "technology", "compliance", "direction", "responsibleArea"])
def test_existing_roles_get_no_inventory_permissions(role):
    with pytest.raises(HTTPException) as error:
        allow(Actor(uuid4(), role), "stock:read")
    assert error.value.status_code == 403


def test_scopes_are_signed_and_role_specific():
    clinic_id, region_id = uuid4(), uuid4()
    token = create_access_token(uuid4(), "inventoryOperator", clinic_ids=(clinic_id,), jurisdiction_ids=(region_id,))
    claims = decode_access_token(token)
    assert claims["clinic_ids"] == [str(clinic_id)]
    clinic = Clinic(id=clinic_id, jurisdiction_id=region_id, is_active=True)
    scope(Actor(uuid4(), "inventoryOperator", clinic_ids=(clinic_id,)), clinic)
    scope(Actor(uuid4(), "inventoryRegional", jurisdiction_ids=(region_id,)), clinic)
    with pytest.raises(HTTPException):
        scope(Actor(uuid4(), "inventoryOperator", jurisdiction_ids=(region_id,)), clinic)
    with pytest.raises(HTTPException):
        allow(Actor(uuid4(), "inventoryRegional"), "movement:write")
    with pytest.raises(HTTPException):
        allow(Actor(uuid4(), "inventoryAdmin"), "movement:write")


def test_http_denies_missing_identity_without_database():
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/inventory/items")
            assert response.status_code == 401
    asyncio.run(run())


def isolated_url():
    url = os.getenv("INVENTORY_TEST_DATABASE_URL", "")
    if not url:
        pytest.skip("INVENTORY_TEST_DATABASE_URL required for isolated PostgreSQL tests")
    if not urlparse(url).path.rsplit("/", 1)[-1].startswith("inventory_validation"):
        raise AssertionError("Inventory tests refuse databases without the inventory_validation prefix")
    return url


async def setup_fixture(session):
    actor_id = uuid4()
    now = datetime.now(UTC)
    def fields(key):
        return dict(key=key, label="Synthetic " + key, created_at=now, updated_at=now, created_by=actor_id, updated_by=actor_id, is_active=True)
    us, uk = Jurisdiction(**fields("SYN-US-" + str(uuid4()))), Jurisdiction(**fields("SYN-UK-" + str(uuid4())))
    session.add_all([us, uk]); await session.flush()
    c1, c2 = Clinic(jurisdiction_id=us.id, **fields("SYN-C1-" + str(uuid4()))), Clinic(jurisdiction_id=uk.id, **fields("SYN-C2-" + str(uuid4())))
    session.add_all([c1, c2]); await session.flush()
    return c1, c2, Actor(actor_id, "inventoryAdmin"), Actor(uuid4(), "inventoryManager", clinic_ids=(c1.id,)), Actor(uuid4(), "inventoryRegional", jurisdiction_ids=(us.id,))


@pytest.mark.integration
def test_inventory_http_lifecycle_lots_history_and_reorder():
    async def run():
        engine = create_async_engine(isolated_url())
        # Outer rollback preserves the database, including append-only histories.
        async with engine.connect() as connection:
            transaction = await connection.begin()
            factory = async_sessionmaker(bind=connection, expire_on_commit=False, join_transaction_mode="create_savepoint")
            async with factory() as session:
                c1, c2, admin, manager, region = await setup_fixture(session)
                await session.commit()
            async def override():
                async with factory() as session:
                    yield session
            app.dependency_overrides[get_session] = override
            try:
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    def headers(actor):
                        return {"Authorization": "Bearer " + create_access_token(actor.id, actor.role, clinic_ids=actor.clinic_ids, jurisdiction_ids=actor.jurisdiction_ids)}
                    async def request(method, path, actor=manager, expected=200, **kwargs):
                        response = await client.request(method, path, headers=headers(actor), **kwargs)
                        assert response.status_code == expected, response.text
                        return response.json()
                    product = await request("POST", "/inventory/items", admin, 201, json=dict(title="Synthetic gauze", product_code="SYN-" + str(uuid4()), unit="piece", pack_label="blister", pack_size=10))
                    iid = product["id"]
                    base = f"/inventory/items/{iid}"
                    await request("POST", base + f"/clinics/{c1.id}/configuration", json={"reorder_point": 20})
                    await request("POST", base + f"/clinics/{c2.id}/configuration", expected=403, json={"reorder_point": 20})
                    await request("PATCH", base, admin, 422, json={"stock": 300})
                    payload = dict(item_id=iid, clinic_id=str(c1.id), kind="in", quantity=3, unit="pack")
                    incoming = await request("POST", "/inventory/movements", expected=201, json=payload)
                    assert incoming["delta"] == 30
                    await request("POST", "/inventory/movements", region, 403, json=payload)
                    await request("POST", "/inventory/movements", expected=409, json={**payload, "kind": "out", "quantity": 4})
                    state = await request("GET", base + "/stock", params={"clinic_id": str(c1.id)})
                    assert state["quantity"] == 30 and not state["below_reorder"] and state["complete_packs"] == 3
                    await request("PATCH", base, admin, json={"pack_size": 5})
                    # Count exactly threshold, then below: equality must not activate reorder.
                    adjust = dict(item_id=iid, clinic_id=str(c1.id), kind="adjust", counted_quantity=20, reason="Synthetic recount")
                    counted = await request("POST", "/inventory/movements", expected=201, json=adjust)
                    assert counted["previous_quantity"] == 30 and counted["delta"] == -10
                    assert await request("GET", "/inventory/reorder", region) == []
                    await request("POST", "/inventory/movements", expected=201, json={**adjust, "counted_quantity": 19})
                    assert (await request("GET", "/inventory/reorder", region))[0]["quantity"] == 19
                    history = await request("GET", base + "/movements", params={"clinic_id": str(c1.id)})
                    assert history[0]["pack_size"] == 10 and history[1]["reason"] == "[REDACTED]"
                    await request("POST", base + "/deactivation", admin, 409, json={"reason": "Synthetic retirement"})
                    await request("POST", f"/inventory/movements/{incoming['id']}/correction", expected=409, json={"reason": "Synthetic mistake"})
                    await request("POST", f"/inventory/movements/{counted['id']}/correction", expected=201, json={"reason": "Synthetic mistake"})
                    await request("POST", f"/inventory/movements/{counted['id']}/correction", expected=409, json={"reason": "Synthetic duplicate"})
                    await request("POST", "/inventory/movements", expected=201, json={**adjust, "counted_quantity": 0})
                    await request("POST", base + "/deactivation", admin, json={"reason": "Synthetic retirement"})
                    assert len(await request("GET", base + "/movements", params={"clinic_id": str(c1.id)})) == 5
                    await request("POST", "/inventory/movements", expected=409, json=payload)
                    assert await request("GET", "/inventory/stock", region, params={"clinic_id": str(c2.id)}, expected=403)
                    # Independent lot balances; no automatic consumption from another lot.
                    lot_item = await request("POST", "/inventory/items", admin, 201, json=dict(title="Synthetic lot item", product_code="LOT-" + str(uuid4()), unit="piece", uses_lots=True))
                    lid = lot_item["id"]
                    await request("POST", f"/inventory/items/{lid}/clinics/{c1.id}/configuration", json={"reorder_point": 5})
                    lots = [await request("POST", f"/inventory/items/{lid}/lots", admin, 201, json={"code": code}) for code in ("SYN-A", "SYN-B")]
                    lp = dict(item_id=lid, clinic_id=str(c1.id), kind="in", quantity=10)
                    await request("POST", "/inventory/movements", expected=422, json=lp)
                    await request("POST", "/inventory/movements", expected=404, json={**lp, "lot_id": str(uuid4())})
                    foreign = await request("POST", "/inventory/items", admin, 201, json=dict(title="Synthetic other lot item", product_code="OTHER-" + str(uuid4()), unit="piece", uses_lots=True))
                    foreign_lot = await request("POST", f"/inventory/items/{foreign['id']}/lots", admin, 201, json={"code": "SYN-FOREIGN"})
                    await request("POST", "/inventory/movements", expected=422, json={**lp, "lot_id": foreign_lot["id"]})
                    await request("POST", "/inventory/movements", expected=404, json={**lp, "item_id": str(uuid4())})
                    await request("POST", "/inventory/movements", expected=201, json={**lp, "lot_id": lots[0]["id"]})
                    await request("POST", "/inventory/movements", expected=409, json={**lp, "lot_id": lots[1]["id"], "kind": "out", "quantity": 1})
                    auditor = Actor(uuid4(), "inventoryAuditor", jurisdiction_ids=region.jurisdiction_ids)
                    events = await request("GET", base + "/audit", auditor, params={"clinic_id": str(c1.id)})
                    assert events and all(e["after_data"] == {"_redacted": True} for e in events)
            finally:
                app.dependency_overrides.pop(get_session, None)
                await transaction.rollback()
        await engine.dispose()
    asyncio.run(run())


@pytest.mark.integration
def test_postgresql_concurrent_exits_and_immutable_history():
    async def run():
        engine = create_async_engine(isolated_url())
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session, session.begin():
            c1, _, admin, manager, _ = await setup_fixture(session)
            value = await svc.create_item(session, admin, ItemCreate(title="Synthetic concurrency", product_code="CONC-" + str(uuid4()), unit="piece"))
            await svc.configure(session, manager, value.id, c1.id, ClinicConfig(reorder_point=5))
            incoming = await svc.movement(session, manager, MovementCreate(item_id=value.id, clinic_id=c1.id, kind="in", quantity=10))
        gate = asyncio.Event()
        entered = 0
        async def exit_once():
            nonlocal entered
            async with factory() as session:
                entered += 1
                if entered == 2: gate.set()
                await gate.wait()
                try:
                    async with session.begin():
                        await svc.movement(session, manager, MovementCreate(item_id=value.id, clinic_id=c1.id, kind="out", quantity=7))
                    return 201
                except HTTPException as error:
                    return error.status_code
        assert sorted(await asyncio.gather(exit_once(), exit_once())) == [201, 409]
        async with factory() as session:
            assert await svc.quantity(session, value.id, c1.id) == 3
            rows = (await session.scalars(select(InventoryMovement).where(InventoryMovement.item_id == value.id))).all()
            assert len(rows) == 2
            await session.rollback()
            with pytest.raises(Exception, match="append-only"):
                async with session.begin():
                    await session.execute(text("UPDATE inventory_movement SET delta=0 WHERE id=:id"), {"id": incoming.id})
        # A cold item has no movement rows to lock: both exits must still fail atomically.
        async with factory() as session, session.begin():
            value = await svc.create_item(session, admin, ItemCreate(title="Synthetic cold balance", product_code="COLD-" + str(uuid4()), unit="piece"))
            await svc.configure(session, manager, value.id, c1.id, ClinicConfig(reorder_point=5))
        entered = 0
        gate = asyncio.Event()
        assert await asyncio.gather(exit_once(), exit_once()) == [409, 409]
        async with factory() as session:
            assert await svc.quantity(session, value.id, c1.id) == 0
            assert (await session.scalars(select(InventoryMovement).where(InventoryMovement.item_id == value.id))).all() == []
        # Records intentionally remain only in this disposable isolated database.
        await engine.dispose()
    asyncio.run(run())
