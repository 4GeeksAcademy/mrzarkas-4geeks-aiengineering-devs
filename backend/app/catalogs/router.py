from app.error_contracts import error_responses
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalogs.cache import catalog_cache
from app.telemetry.request_producer import mark_authenticated_general_request
from app.catalogs.schemas import CatalogResponse, CatalogValueResponse
from app.auth.dependencies import Actor, require_capability
from app.db.models.catalog import Catalog, CatalogValue
from app.db.session import get_session

router = APIRouter(prefix="/catalogs", tags=["catalogs"], responses=error_responses(401, 403))


@router.get("/{catalog_name}", response_model=CatalogResponse, responses=error_responses(404))
async def get_catalog(
    catalog_name: str,
    session: AsyncSession = Depends(get_session),
    actor: Actor = Depends(require_capability("catalog:read")),
    request: Request = None,
) -> CatalogResponse:
    catalog = (
        await session.execute(
            select(Catalog).where(
                Catalog.catalog_name == catalog_name,
                Catalog.is_active.is_(True),
            )
        )
    ).scalar_one_or_none()
    if catalog is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Catalog not found",
        )

    # Cache all active flags and date ranges, then project using the current UTC
    # instant on EVERY read. Future activations/expiry need no write or stale TTL.
    generation = (catalog.version, catalog.updated_at.isoformat())
    key = catalog_cache.key("active", actor, catalog.id, generation)

    async def load():
        rows = (await session.execute(select(CatalogValue).where(
            CatalogValue.catalog_id == catalog.id
        ).order_by(CatalogValue.sort_order, CatalogValue.key))).scalars().all()
        return [{"active": row.is_active, "value": CatalogValueResponse.model_validate(row).model_dump(mode="json")} for row in rows]

    async def still_current():
        row = (await session.execute(select(Catalog.version, Catalog.updated_at, Catalog.is_active).where(Catalog.id == catalog.id))).one_or_none()
        return row is not None and (row.version, row.updated_at.isoformat()) == generation and row.is_active

    rows = await catalog_cache.read(key, 60, load, still_current)
    now = datetime.now(UTC)
    values = [CatalogValueResponse.model_validate(row["value"]) for row in rows if row["active"]]
    response = CatalogResponse(catalog_name=catalog.catalog_name, version=catalog.version, values=[
        value for value in values if value.effective_from <= now and (value.effective_to is None or value.effective_to >= now)
    ])

    mark_authenticated_general_request(request, actor, "catalogs")
    return response
