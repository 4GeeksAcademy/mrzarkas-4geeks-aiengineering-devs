"""Add Management audit infrastructure.

Revision ID: 0009_management_audit
Revises: 0008_compliance_review
"""

from alembic import op
import sqlalchemy as sa


revision = "0009_management_audit"
down_revision = "0008_compliance_review"
branch_labels = None
depends_on = None

SYSTEM_ACTOR_ID = "00000000-0000-0000-0000-000000000900"
REFERENCE_TABLES = (
    "reference_jurisdiction",
    "reference_responsible_area",
    "reference_affected_system",
    "reference_clinic",
)


def upgrade() -> None:
    for table in REFERENCE_TABLES:
        op.add_column(table, sa.Column("created_at", sa.DateTime(timezone=True), nullable=True))
        op.add_column(table, sa.Column("created_by", sa.Uuid(), nullable=True))
        op.add_column(table, sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
        op.add_column(table, sa.Column("updated_by", sa.Uuid(), nullable=True))
        op.execute(
            sa.text(
                f"UPDATE {table} SET created_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP, "
                f"created_by = '{SYSTEM_ACTOR_ID}', updated_by = '{SYSTEM_ACTOR_ID}' "
                "WHERE created_at IS NULL"
            )
        )
        op.alter_column(table, "created_at", nullable=False)
        op.alter_column(table, "created_by", nullable=False)
        op.alter_column(table, "updated_at", nullable=False)
        op.alter_column(table, "updated_by", nullable=False)

    op.create_table(
        "management_audit_event",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=False),
        sa.Column("resource_id", sa.Uuid(), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("before_data", sa.JSON(), nullable=True),
        sa.Column("after_data", sa.JSON(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("correlation_id", sa.Uuid(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_management_audit_event_resource_occurred_at",
        "management_audit_event",
        ["resource_type", "resource_id", "occurred_at"],
    )
    op.create_index(
        "ix_management_audit_event_actor_occurred_at",
        "management_audit_event",
        ["actor_id", "occurred_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_management_audit_event_actor_occurred_at", table_name="management_audit_event")
    op.drop_index("ix_management_audit_event_resource_occurred_at", table_name="management_audit_event")
    op.drop_table("management_audit_event")
    for table in reversed(REFERENCE_TABLES):
        op.drop_column(table, "updated_by")
        op.drop_column(table, "updated_at")
        op.drop_column(table, "created_by")
        op.drop_column(table, "created_at")
