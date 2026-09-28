from uuid import UUID

from sqlalchemy import select

from app.db.session import SessionLocal
from app.reference_data.models import AffectedSystem, Clinic, Jurisdiction, ResponsibleArea


async def reference_ids() -> dict[str, UUID]:
    """Return the stable synthetic reference IDs seeded for integration tests."""
    if SessionLocal is None:
        return {}
    async with SessionLocal() as session:
        rows = []
        for model in (Clinic, Jurisdiction, AffectedSystem, ResponsibleArea):
            rows.extend((await session.execute(select(model.key, model.id))).all())
        return dict(rows)
