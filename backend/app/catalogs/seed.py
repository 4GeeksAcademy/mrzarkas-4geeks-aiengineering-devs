from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select

from app.db.models.catalog import Catalog, CatalogValue
from app.db.session import SessionLocal


# Stable technical actor used only for bootstrap data. It is not a real person.
SEED_ACTOR_ID = UUID("00000000-0000-0000-0000-000000000001")

CATALOGS: dict[str, list[tuple[object, ...]]] = {
    "entryChannel": [
        ("clinicPhone", "Teléfono de clínica"),
        ("email", "Correo electrónico"),
        ("backofficeForm", "Formulario de backoffice"),
        ("technicalMonitoring", "Monitorización técnica"),
        ("internalEscalation", "Escalado interno"),
        ("other", "Otro"),
    ],
    "incidentType": [
        ("systemAvailability", "Disponibilidad del sistema"),
        ("performanceDegradation", "Degradación de rendimiento"),
        ("functionalError", "Error funcional"),
        ("integration", "Integración"),
        ("accessOrAuthentication", "Acceso o autenticación"),
        ("dataOrSynchronization", "Datos o sincronización"),
        ("complianceOrAudit", "Cumplimiento o auditoría"),
        ("billingOrClaim", "Facturación o reclamación"),
        ("appointmentOrScheduling", "Citas y agenda"),
    ],
    "severity": [
        ("critical", "Crítica"),
        ("high", "Alta"),
        ("medium", "Media"),
        ("low", "Baja"),
    ],
    "incidentStatus": [
        ("new", "Nueva", True),
        ("underAnalysis", "En análisis", True),
        ("assigned", "Asignada", True),
        ("inResolution", "En resolución", True),
        ("resolved", "Resuelta", False),
        ("closed", "Cerrada", False),
        ("onHold", "En espera", True),
        ("reopened", "Reabierta", True),
        ("cancelled", "Cancelada", False),
    ],
}


async def seed_catalogs() -> None:
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL is required to seed catalogs")

    now = datetime.now(UTC)
    async with SessionLocal() as session:
        for catalog_name, raw_values in CATALOGS.items():
            catalog_id = uuid4()
            catalog_stmt = insert(Catalog).values(
                id=catalog_id,
                catalog_name=catalog_name,
                version=1,
                is_active=True,
                created_at=now,
                created_by=SEED_ACTOR_ID,
                updated_at=now,
                updated_by=SEED_ACTOR_ID,
            )
            catalog_stmt = catalog_stmt.on_conflict_do_nothing(
                index_elements=[Catalog.catalog_name]
            )
            await session.execute(catalog_stmt)

            persisted_catalog_id = (
                await session.execute(
                    select(Catalog.id).where(
                        Catalog.catalog_name == catalog_name
                    )
                )
            ).scalar_one()

            values = []
            for sort_order, raw_value in enumerate(raw_values):
                key, label, *open_value = raw_value
                values.append(
                    {
                        "id": uuid4(),
                        "catalog_id": persisted_catalog_id,
                        "key": key,
                        "label": label,
                        "description": None,
                        "is_active": True,
                        "is_open": open_value[0] if open_value else None,
                        "sort_order": sort_order,
                        "effective_from": now,
                        "effective_to": None,
                        "created_at": now,
                        "created_by": SEED_ACTOR_ID,
                        "updated_at": now,
                        "updated_by": SEED_ACTOR_ID,
                    }
                )

            value_stmt = insert(CatalogValue).values(values)
            value_stmt = value_stmt.on_conflict_do_update(
                index_elements=[CatalogValue.catalog_id, CatalogValue.key],
                set_={
                    "label": value_stmt.excluded.label,
                    "description": value_stmt.excluded.description,
                    "is_open": value_stmt.excluded.is_open,
                    "sort_order": value_stmt.excluded.sort_order,
                    "updated_at": now,
                    "updated_by": SEED_ACTOR_ID,
                },
            )
            await session.execute(value_stmt)

        await session.commit()


def main() -> None:
    asyncio.run(seed_catalogs())


if __name__ == "__main__":
    main()