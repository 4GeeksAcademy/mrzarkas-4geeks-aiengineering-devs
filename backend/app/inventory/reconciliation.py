"""Read-only projection check against an independent bounded ledger sum."""
import asyncio
from dataclasses import dataclass
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from app.db import session as database
from app.inventory.models import InventoryMovement, InventoryItem
from app.inventory.policies import allow
from app.inventory import service
from app.reference_data.models import Clinic, Jurisdiction

LIMIT = 10000


@dataclass(frozen=True)
class Check:
    result: str
    region: str | None = None


def compare(projected, rows, country_id, country_key, lot_id=None):
    if len(rows) > LIMIT or any(row.jurisdiction_id != country_id or row.jurisdiction_key != country_key for row in rows):
        return 'inconclusive'
    total = sum(row.delta for row in rows if lot_id is None or row.lot_id == lot_id)
    return 'matched' if projected.quantity == total else 'mismatched'


async def _check(actor, item_id, clinic_id, lot_id):
    if database.engine is None:
        return Check('inconclusive')
    async with database.engine.connect() as connection:
        connection = await connection.execution_options(isolation_level='REPEATABLE READ')
        async with connection.begin():
            await connection.execute(text('SET TRANSACTION READ ONLY'))
            await connection.execute(text("SET LOCAL statement_timeout = '900ms'"))
            async with AsyncSession(bind=connection) as session:
                projected = await service.stock(session,actor,item_id,clinic_id,lot_id)
                item = await session.get(InventoryItem,item_id)
                if not item.is_active:
                    raise HTTPException(409, 'Item is inactive')
                clinic = await session.get(Clinic,clinic_id)
                country = await session.get(Jurisdiction,clinic.jurisdiction_id)
                if country is None or not country.is_active or country.key not in {'US','UK'}:
                    return Check('inconclusive')
                rows = (await session.execute(select(InventoryMovement.delta,InventoryMovement.lot_id,
                    InventoryMovement.jurisdiction_id,InventoryMovement.jurisdiction_key).where(
                    InventoryMovement.item_id==item_id,InventoryMovement.clinic_id==clinic_id)
                    .order_by(InventoryMovement.id).limit(LIMIT+1))).all()
                return Check(compare(projected,rows,country.id,country.key,lot_id),country.key)


async def check(actor,item_id,clinic_id,lot_id=None):
    allow(actor,'audit:read')
    allow(actor,'stock:read')
    try:
        return await asyncio.wait_for(_check(actor,item_id,clinic_id,lot_id),timeout=1)
    except HTTPException:
        raise
    except (SQLAlchemyError,OSError,TimeoutError):
        return Check('inconclusive')
