from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CatalogValueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    key: str
    label: str
    description: str | None
    is_open: bool | None
    sort_order: int
    effective_from: datetime
    effective_to: datetime | None


class CatalogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    catalog_name: str
    version: int
    values: list[CatalogValueResponse]