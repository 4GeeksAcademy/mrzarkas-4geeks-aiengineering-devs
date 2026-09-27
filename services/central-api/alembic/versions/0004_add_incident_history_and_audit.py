"""Add incident status history and audit events.

Revision ID: 0004_history_audit
Revises: 0003_create_operational_incident
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Alembic's default version table uses VARCHAR(32). Keep revision IDs within
# that limit so the version update succeeds on PostgreSQL.
revision: str = "0004_history_audit"
down_revision: Union[str, None] = "0003_create_operational_incident"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "incident_status_history",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("incident_id", sa.Uuid(), nullable=False),
        sa.Column("from_status_value_id", sa.Uuid(), nullable=True),
        sa.Column("to_status_value_id", sa.Uuid(), nullable=False),
        sa.Column("changed_by", sa.Uuid(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["incident_id"], ["operational_incident.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["from_status_value_id"], ["catalog_value.id"]),
        sa.ForeignKeyConstraint(["to_status_value_id"], ["catalog_value.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_incident_status_history_incident", "incident_status_history", ["incident_id", "changed_at"])

    op.create_table(
        "audit_event",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("before_data", sa.JSON(), nullable=True),
        sa.Column("after_data", sa.JSON(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_event_entity", "audit_event", ["entity_type", "entity_id", "occurred_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_event_entity", table_name="audit_event")
    op.drop_table("audit_event")
    op.drop_index("ix_incident_status_history_incident", table_name="incident_status_history")
    op.drop_table("incident_status_history")
