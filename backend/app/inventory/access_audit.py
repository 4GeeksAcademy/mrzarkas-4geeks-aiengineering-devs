"""Durable authenticated inventory denials; never retain body, headers or tokens."""
from uuid import UUID

from fastapi import Depends, HTTPException, Request
from fastapi.routing import APIRoute
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import Actor, get_current_actor
from app.db.session import get_session
from app.reference_data.models import Clinic, Jurisdiction
from .models import InventoryAccessDenial, InventoryItem, InventoryMovement


async def inventory_actor(request: Request, actor: Actor = Depends(get_current_actor)):
    request.state.inventory_actor = actor
    return actor


async def inventory_session(request: Request, session: AsyncSession = Depends(get_session)):
    request.state.inventory_session = session
    return session


def identifier(value):
    try:
        return UUID(str(value)) if value is not None else None
    except (TypeError, ValueError):
        return None


async def record_denial(request, operation, reason_code):
    session = getattr(request.state, "inventory_session", None)
    actor = getattr(request.state, "inventory_actor", None)
    if session is None or actor is None:
        raise HTTPException(503, "Inventory denial audit unavailable")
    # Only UUID references from already parsed requests are considered. Validation
    # against the database, not caller claims, determines the persisted country.
    values = dict(request.query_params)
    values.update(request.path_params)
    if request.method in {"POST", "PATCH"}:
        try:
            body = await request.json()
            if isinstance(body, dict):
                for key in ("item_id", "clinic_id"):
                    if key in body:
                        values[key] = body[key]
        except (ValueError, TypeError):
            pass
    item_id, clinic_id = identifier(values.get("item_id")), identifier(values.get("clinic_id"))
    await session.rollback()
    async with session.begin():
        movement_id = identifier(values.get("movement_id"))
        if movement_id is not None:
            movement = await session.get(InventoryMovement, movement_id)
            if movement is not None:
                item_id, clinic_id = movement.item_id, movement.clinic_id
        item = await session.get(InventoryItem, item_id) if item_id else None
        clinic = await session.get(Clinic, clinic_id) if clinic_id else None
        country = await session.get(Jurisdiction, clinic.jurisdiction_id) if clinic else None
        session.add(InventoryAccessDenial(actor_id=actor.id, operation=operation,
            reason_code=reason_code, result="denied", item_id=item.id if item else None,
            clinic_id=clinic.id if clinic else None, jurisdiction_id=country.id if country else None,
            jurisdiction_key=country.key if country else None))
        await session.flush()


class InventoryRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()

        async def audited(request):
            try:
                return await handler(request)
            except HTTPException as error:
                if error.status_code != 403:
                    raise
                try:
                    await record_denial(request, self.name,
                        "scope" if error.detail == "Clinic outside inventory scope" else "permission")
                except (SQLAlchemyError, RuntimeError, HTTPException) as failure:
                    # No operation is allowed, and absence of required durable
                    # evidence is explicitly surfaced rather than silently lost.
                    raise HTTPException(503, "Inventory denial audit unavailable") from failure
                raise

        return audited
