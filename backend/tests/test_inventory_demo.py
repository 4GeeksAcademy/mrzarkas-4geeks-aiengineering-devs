import asyncio
from types import SimpleNamespace

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.inventory import demo, service
from app.inventory.models import InventoryItem, InventoryMovement
from app.inventory.schemas import MovementCreate
from app.auth.dependencies import Actor
from app.reference_data import seed
from test_inventory import isolated_url


@pytest.mark.parametrize("environment", ["staging", "production"])
def test_demo_refuses_shared_environments(monkeypatch, environment):
    monkeypatch.setattr(demo, "get_settings", lambda: SimpleNamespace(app_environment=environment))
    with pytest.raises(RuntimeError, match="restricted"):
        asyncio.run(demo.seed_demo())


@pytest.mark.integration
def test_demo_preserves_changed_balances_on_repeat_and_rejects_conflicts(monkeypatch):
    async def run():
        engine = create_async_engine(isolated_url())
        async with engine.connect() as connection:
            outer = await connection.begin()
            factory = async_sessionmaker(connection, expire_on_commit=False, join_transaction_mode="create_savepoint")
            monkeypatch.setattr(seed, "SessionLocal", factory)
            monkeypatch.setattr(demo, "SessionLocal", factory)
            await seed.seed_reference_data()
            assert await demo.seed_demo() == 6
            async with factory() as session, session.begin():
                item = await session.scalar(select(InventoryItem).where(InventoryItem.product_code == "SYN-INV-GAUZE"))
                await service.movement(session, Actor(demo.ACTOR_ID, "inventoryManager", clinic_ids=(seed.US_CLINIC,)),
                    MovementCreate(item_id=item.id, clinic_id=seed.US_CLINIC, kind="out", quantity=1))
            assert await demo.seed_demo() == 0
            async with factory() as session:
                assert await service.quantity(session, item.id, seed.US_CLINIC) == 9
                count = await session.scalar(select(func.count()).select_from(InventoryMovement))
                item = await session.get(InventoryItem, item.id)
                item.title = "Changed synthetic title"
                await session.commit()
            with pytest.raises(RuntimeError, match="conflicts"):
                await demo.seed_demo()
            async with factory() as session:
                assert await session.scalar(select(func.count()).select_from(InventoryMovement)) == count
            await outer.rollback()
        await engine.dispose()
    asyncio.run(run())
