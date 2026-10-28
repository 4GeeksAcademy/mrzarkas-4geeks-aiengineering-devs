"""Create ComplianceReview and link incidents.

Revision ID: 0008_compliance_review
Revises: 0007_incident_reference_fks
"""
from alembic import op
import sqlalchemy as sa

revision = "0008_compliance_review"
down_revision = "0007_incident_reference_fks"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "compliance_review",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("review_identifier", sa.String(length=40), nullable=False),
        sa.Column("jurisdiction_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["jurisdiction_id"], ["reference_jurisdiction.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("review_identifier"),
    )
    op.create_foreign_key("fk_incident_compliance_review", "operational_incident", "compliance_review", ["compliance_review_id"], ["id"])

def downgrade() -> None:
    op.drop_constraint("fk_incident_compliance_review", "operational_incident", type_="foreignkey")
    op.drop_table("compliance_review")
