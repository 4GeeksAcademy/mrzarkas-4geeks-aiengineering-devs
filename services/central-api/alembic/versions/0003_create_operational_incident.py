"""Create the operational incident table.

Revision ID: 0003_create_operational_incident
Revises: 0002_create_catalog_tables
Create Date: 2026-09-26
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_create_operational_incident"
down_revision: Union[str, None] = "0002_create_catalog_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "operational_incident",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("incident_identifier", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("reporter_id", sa.Uuid(), nullable=False),
        sa.Column("clinic_id", sa.Uuid(), nullable=False),
        sa.Column("jurisdiction_id", sa.Uuid(), nullable=False),
        sa.Column("affected_system_id", sa.Uuid(), nullable=False),
        sa.Column("entry_channel_value_id", sa.Uuid(), nullable=False),
        sa.Column("incident_type_value_id", sa.Uuid(), nullable=False),
        sa.Column("severity_value_id", sa.Uuid(), nullable=False),
        sa.Column("status_value_id", sa.Uuid(), nullable=False),
        sa.Column("responsible_area_id", sa.Uuid(), nullable=False),
        sa.Column("compliance_review_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["entry_channel_value_id"], ["catalog_value.id"]),
        sa.ForeignKeyConstraint(["incident_type_value_id"], ["catalog_value.id"]),
        sa.ForeignKeyConstraint(["severity_value_id"], ["catalog_value.id"]),
        sa.ForeignKeyConstraint(["status_value_id"], ["catalog_value.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("incident_identifier", name="uq_operational_incident_identifier"),
    )
    op.create_index("ix_operational_incident_status", "operational_incident", ["status_value_id"])
    op.create_index("ix_operational_incident_severity", "operational_incident", ["severity_value_id"])
    op.create_index("ix_operational_incident_area", "operational_incident", ["responsible_area_id"])
    op.create_index("ix_operational_incident_created_at", "operational_incident", ["created_at"])
    op.create_index("ix_operational_incident_updated_at", "operational_incident", ["updated_at"])


def downgrade() -> None:
    op.drop_index("ix_operational_incident_updated_at", table_name="operational_incident")
    op.drop_index("ix_operational_incident_created_at", table_name="operational_incident")
    op.drop_index("ix_operational_incident_area", table_name="operational_incident")
    op.drop_index("ix_operational_incident_severity", table_name="operational_incident")
    op.drop_index("ix_operational_incident_status", table_name="operational_incident")
    op.drop_table("operational_incident")