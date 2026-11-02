"""Historical country and denial evidence. Legacy country stays explicitly unknown."""
from alembic import op
import sqlalchemy as sa

revision = "0011_inventory_audit_policy"
down_revision = "0010_inventory"
branch_labels = None
depends_on = None


def upgrade():
    for table in ("inventory_movement", "inventory_audit"):
        op.add_column(table, sa.Column("jurisdiction_id", sa.Uuid(), nullable=True))
        op.create_foreign_key(f"fk_{table}_country", table, "reference_jurisdiction", ["jurisdiction_id"], ["id"])
        op.add_column(table, sa.Column("jurisdiction_key", sa.String(100), nullable=True))
        op.add_column(table, sa.Column("result", sa.String(20), nullable=False, server_default="accepted"))
        op.alter_column(table, "result", server_default=None)
    op.create_table("inventory_access_denial",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("operation", sa.String(80), nullable=False),
        sa.Column("reason_code", sa.String(20), nullable=False),
        sa.Column("result", sa.String(20), nullable=False),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("reference_clinic.id")),
        sa.Column("item_id", sa.Uuid(), sa.ForeignKey("inventory_item.id")),
        sa.Column("jurisdiction_id", sa.Uuid(), sa.ForeignKey("reference_jurisdiction.id")),
        sa.Column("jurisdiction_key", sa.String(100)),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("result = 'denied'", name="inventory_denial_result"))
    op.create_index("ix_inventory_denial_country_time", "inventory_access_denial", ["jurisdiction_id", "occurred_at", "id"])
    op.execute("CREATE TRIGGER inventory_access_denial_immutable BEFORE UPDATE OR DELETE ON inventory_access_denial FOR EACH ROW EXECUTE FUNCTION inventory_preserve_history()")


def downgrade():
    # Only for an explicitly authorized disposable schema/restore procedure.
    op.drop_table("inventory_access_denial")
    for table in ("inventory_audit", "inventory_movement"):
        op.drop_column(table, "result")
        op.drop_column(table, "jurisdiction_key")
        op.drop_constraint(f"fk_{table}_country", table, type_="foreignkey")
        op.drop_column(table, "jurisdiction_id")
