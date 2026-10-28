"""Create configurable catalog tables.

Revision ID: 0002_create_catalog_tables
Revises: 0001_initial_schema
Create Date: 2026-09-26
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_create_catalog_tables"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "catalog",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("catalog_name", sa.String(length=100), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by", sa.Uuid(), nullable=False),
        sa.CheckConstraint("version > 0", name="ck_catalog_version_positive"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("catalog_name"),
    )
    op.create_table(
        "catalog_value",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("catalog_id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("label", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_open", sa.Boolean(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by", sa.Uuid(), nullable=False),
        sa.CheckConstraint("sort_order >= 0", name="ck_catalog_value_sort_order_nonnegative"),
        sa.CheckConstraint(
            "effective_to IS NULL OR effective_to >= effective_from",
            name="ck_catalog_value_effective_range",
        ),
        sa.ForeignKeyConstraint(["catalog_id"], ["catalog.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("catalog_id", "key", name="uq_catalog_value_catalog_key"),
    )


def downgrade() -> None:
    op.drop_table("catalog_value")
    op.drop_table("catalog")