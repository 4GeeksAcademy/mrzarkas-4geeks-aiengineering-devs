"""Add incident assignment history.

Revision ID: 0005_assignment_history
Revises: 0004_history_audit
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0005_assignment_history"
down_revision: Union[str, None] = "0004_history_audit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "incident_assignment_history",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("incident_id", sa.Uuid(), nullable=False),
        sa.Column("from_responsible_area_id", sa.Uuid(), nullable=True),
        sa.Column("to_responsible_area_id", sa.Uuid(), nullable=False),
        sa.Column("changed_by", sa.Uuid(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["incident_id"], ["operational_incident.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_incident_assignment_history_incident",
        "incident_assignment_history",
        ["incident_id", "changed_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_incident_assignment_history_incident", table_name="incident_assignment_history")
    op.drop_table("incident_assignment_history")
