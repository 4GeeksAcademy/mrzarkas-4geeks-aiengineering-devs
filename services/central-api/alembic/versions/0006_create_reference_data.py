"""Create shared reference-data tables.

Revision ID: 0006_reference_data
Revises: 0005_assignment_history
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0006_reference_data"
down_revision: Union[str, None] = "0005_assignment_history"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _base_table(name: str) -> None:
    op.create_table(
        name,
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("label", sa.String(length=200), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key", name=f"uq_{name}_key"),
    )


def upgrade() -> None:
    _base_table("reference_jurisdiction")
    _base_table("reference_responsible_area")
    _base_table("reference_affected_system")
    op.create_table(
        "reference_clinic",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("label", sa.String(length=200), nullable=False),
        sa.Column("jurisdiction_id", sa.Uuid(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["jurisdiction_id"], ["reference_jurisdiction.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key", name="uq_reference_clinic_key"),
    )
    op.create_table(
        "reference_affected_system_jurisdiction",
        sa.Column("affected_system_id", sa.Uuid(), nullable=False),
        sa.Column("jurisdiction_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["affected_system_id"], ["reference_affected_system.id"]),
        sa.ForeignKeyConstraint(["jurisdiction_id"], ["reference_jurisdiction.id"]),
        sa.PrimaryKeyConstraint("affected_system_id", "jurisdiction_id"),
    )


def downgrade() -> None:
    op.drop_table("reference_affected_system_jurisdiction")
    op.drop_table("reference_clinic")
    op.drop_table("reference_affected_system")
    op.drop_table("reference_responsible_area")
    op.drop_table("reference_jurisdiction")
