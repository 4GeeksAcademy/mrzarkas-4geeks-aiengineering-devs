"""Synthetic development fixtures for shared reference data.

Never use these values as the production registry of HealthCore clinics.
"""

import asyncio
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select

from app.db.session import SessionLocal
from app.reference_data.models import AffectedSystem, Clinic, Jurisdiction, ResponsibleArea, affected_system_jurisdiction


US = UUID("00000000-0000-0000-0000-000000000001")
UK = UUID("00000000-0000-0000-0000-000000000002")
US_CLINIC = UUID("00000000-0000-0000-0000-000000000101")
UK_CLINIC = UUID("00000000-0000-0000-0000-000000000102")
SYSTEM_ACTOR_ID = UUID("00000000-0000-0000-0000-000000000900")
AREAS = [
    (UUID("00000000-0000-0000-0000-000000000201"), "technology", "Technology"),
    (UUID("00000000-0000-0000-0000-000000000202"), "clinicalOperations", "Clinical Operations"),
    (UUID("00000000-0000-0000-0000-000000000203"), "patientAccess", "Patient Access"),
    (UUID("00000000-0000-0000-0000-000000000204"), "revenueCycle", "Revenue Cycle"),
    (UUID("00000000-0000-0000-0000-000000000205"), "compliance", "Compliance and Data Governance"),
]
SYSTEMS = [
    (UUID("00000000-0000-0000-0000-000000000301"), "usEhr", "US EHR", US),
    (UUID("00000000-0000-0000-0000-000000000302"), "usBilling", "US Billing", US),
    (UUID("00000000-0000-0000-0000-000000000303"), "usPhoneScheduling", "US Phone Scheduling", US),
    (UUID("00000000-0000-0000-0000-000000000304"), "ukEhr", "UK EHR", UK),
    (UUID("00000000-0000-0000-0000-000000000305"), "ukBillingSpreadsheet", "UK Billing Spreadsheet", UK),
    (UUID("00000000-0000-0000-0000-000000000306"), "ukManualScheduling", "UK Manual Scheduling", UK),
]


async def seed_reference_data() -> None:
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL is required to seed reference data")
    async with SessionLocal() as session:
        now = datetime.now(UTC)
        audit = {
            "created_at": now,
            "created_by": SYSTEM_ACTOR_ID,
            "updated_at": now,
            "updated_by": SYSTEM_ACTOR_ID,
        }
        for model, values in (
            (Jurisdiction, [{"id": US, "key": "US", "label": "United States", "is_active": True, **audit}, {"id": UK, "key": "UK", "label": "United Kingdom", "is_active": True, **audit}]),
            (ResponsibleArea, [{"id": id, "key": key, "label": label, "is_active": True, **audit} for id, key, label in AREAS]),
            (AffectedSystem, [{"id": id, "key": key, "label": label, "is_active": True, **audit} for id, key, label, _ in SYSTEMS]),
        ):
            await session.execute(insert(model).values(values).on_conflict_do_nothing(index_elements=[model.key]))
        await session.execute(insert(Clinic).values([
            {"id": US_CLINIC, "key": "dev-us-clinic-01", "label": "Development US Clinic", "jurisdiction_id": US, "is_active": True, **audit},
            {"id": UK_CLINIC, "key": "dev-uk-clinic-01", "label": "Development UK Clinic", "jurisdiction_id": UK, "is_active": True, **audit},
        ]).on_conflict_do_nothing(index_elements=[Clinic.key]))
        await session.commit()

        systems = dict((await session.execute(select(AffectedSystem.key, AffectedSystem.id))).all())
        for _, key, _, jurisdiction_id in SYSTEMS:
            await session.execute(insert(affected_system_jurisdiction).values(
                affected_system_id=systems[key], jurisdiction_id=jurisdiction_id
            ).on_conflict_do_nothing())
        await session.commit()


def main() -> None:
    asyncio.run(seed_reference_data())
