"""Idempotent synthetic inventory for the two existing development clinics."""
import asyncio
from uuid import UUID

from sqlalchemy import select

from app.auth.dependencies import Actor
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.reference_data.models import Clinic
from . import service
from .models import InventoryItem, InventoryLot, InventoryMovement
from .schemas import ClinicConfig, ItemCreate, LotCreate, MovementCreate

ACTOR_ID = UUID("00000000-0000-0000-0000-000000009001")
OPENING_REASON = "Synthetic inventory demonstration opening"
PRODUCTS = (
    ("SYN-INV-GAUZE", "Synthetic gauze", "piece", "blister", 10, False, 20, (10, 40)),
    ("SYN-INV-GLOVES", "Synthetic gloves", "pair", "box", 50, False, 30, (100, 20)),
    ("SYN-INV-LOT", "Synthetic lot consumable", "piece", None, 1, True, 10, (25, 5)),
)


async def seed_demo():
    if get_settings().app_environment not in {"development", "test"}:
        raise RuntimeError("Synthetic inventory is restricted to development/test")
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL is required")
    async with SessionLocal() as session:
        async with session.begin():
            clinics = []
            for key in ("dev-us-clinic-01", "dev-uk-clinic-01"):
                clinic = await session.scalar(select(Clinic).where(Clinic.key == key).with_for_update())
                if clinic is None:
                    raise RuntimeError("Run seed-reference-data first")
                clinics.append(clinic)
            admin = Actor(ACTOR_ID, "inventoryAdmin")
            manager = Actor(ACTOR_ID, "inventoryManager", clinic_ids=tuple(c.id for c in clinics))
            created = 0
            for code, title, unit, pack, size, lots, threshold, balances in PRODUCTS:
                payload = ItemCreate(title=title, product_code=code, unit=unit,
                                     pack_label=pack, pack_size=size, uses_lots=lots)
                item = await session.scalar(select(InventoryItem).where(InventoryItem.product_code == code).with_for_update())
                if item is None:
                    item = await service.create_item(session, admin, payload)
                elif item.created_by != ACTOR_ID or any(getattr(item, k) != v for k, v in payload.model_dump().items()) or not item.is_active:
                    raise RuntimeError("Demo product conflicts with existing catalog; nothing committed")
                lot_id = None
                if lots:
                    lot = await session.scalar(select(InventoryLot).where(InventoryLot.item_id == item.id, InventoryLot.code == "SYN-DEMO-LOT-01"))
                    if lot is None:
                        lot = await service.create_lot(session, admin, item.id, LotCreate(code="SYN-DEMO-LOT-01"))
                    lot_id = lot.id
                for clinic, balance in zip(clinics, balances):
                    opening = await session.scalar(select(InventoryMovement.id).where(
                        InventoryMovement.item_id == item.id, InventoryMovement.clinic_id == clinic.id,
                        InventoryMovement.actor_id == ACTOR_ID, InventoryMovement.reason == OPENING_REASON))
                    if opening is not None:
                        continue  # Never reset balances or reorder settings on a repeat run.
                    await service.configure(session, manager, item.id, clinic.id, ClinicConfig(reorder_point=threshold))
                    await service.movement(session, manager, MovementCreate(item_id=item.id,
                        clinic_id=clinic.id, lot_id=lot_id, kind="in", quantity=balance, reason=OPENING_REASON))
                    created += 1
        return created


def main():
    print(f"Synthetic opening movements created: {asyncio.run(seed_demo())}")


if __name__ == "__main__":
    main()
