"""Add OperationalIncident reference-data foreign keys.

Revision ID: 0007_incident_reference_fks
Revises: 0006_reference_data
"""
from alembic import op

revision = "0007_incident_reference_fks"
down_revision = "0006_reference_data"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_foreign_key("fk_incident_clinic", "operational_incident", "reference_clinic", ["clinic_id"], ["id"])
    op.create_foreign_key("fk_incident_jurisdiction", "operational_incident", "reference_jurisdiction", ["jurisdiction_id"], ["id"])
    op.create_foreign_key("fk_incident_system", "operational_incident", "reference_affected_system", ["affected_system_id"], ["id"])
    op.create_foreign_key("fk_incident_area", "operational_incident", "reference_responsible_area", ["responsible_area_id"], ["id"])

def downgrade() -> None:
    op.drop_constraint("fk_incident_area", "operational_incident", type_="foreignkey")
    op.drop_constraint("fk_incident_system", "operational_incident", type_="foreignkey")
    op.drop_constraint("fk_incident_jurisdiction", "operational_incident", type_="foreignkey")
    op.drop_constraint("fk_incident_clinic", "operational_incident", type_="foreignkey")
