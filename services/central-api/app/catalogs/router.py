from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalogs.schemas import CatalogResponse, CatalogValueResponse
from app.db.models.catalog import Catalog, CatalogValue
from app.db.session import get_session

router = APIRouter(prefix="/catalogs", tags=["catalogs"])


@router.get("/{catalog_name}", response_model=CatalogResponse)
async def get_catalog(
    catalog_name: str,
    session: AsyncSession = Depends(get_session),
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

    now = datetime.now(UTC)
    values = (
        await session.execute(
            select(CatalogValue)
            .where(
                CatalogValue.catalog_id == catalog.id,
                CatalogValue.is_active.is_(True),
                CatalogValue.effective_from <= now,
                (CatalogValue.effective_to.is_(None) | (CatalogValue.effective_to >= now)),
            )
            .order_by(CatalogValue.sort_order, CatalogValue.key)
        )
    ).scalars().all()

    return CatalogResponse(
        catalog_name=catalog.catalog_name,
        version=catalog.version,
        values=[CatalogValueResponse.model_validate(value) for value in values],
    )