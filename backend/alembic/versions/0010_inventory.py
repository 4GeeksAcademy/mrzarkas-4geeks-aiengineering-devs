"""Clinic inventory, append-only movements and audit. No existing data changed."""
from alembic import op
import sqlalchemy as sa

revision = "0010_inventory"
down_revision = "0009_management_audit"
branch_labels = None
depends_on = None


def identity():
    return sa.Column("id", sa.Uuid(), primary_key=True)


def reference(name, target, **kw):
    return sa.Column(name, sa.Uuid(), sa.ForeignKey(target), **kw)


def upgrade():
    op.create_table("inventory_item", identity(),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("product_code", sa.String(100), unique=True, nullable=False),
        sa.Column("unit", sa.String(80), nullable=False),
        sa.Column("uses_lots", sa.Boolean(), nullable=False),
        sa.Column("pack_label", sa.String(80)),
        sa.Column("pack_size", sa.BigInteger(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.CheckConstraint("pack_size > 0", name="inventory_pack_positive"))
    op.create_table("inventory_clinic_item",
        reference("item_id", "inventory_item.id", primary_key=True),
        reference("clinic_id", "reference_clinic.id", primary_key=True),
        sa.Column("reorder_point", sa.BigInteger(), nullable=False),
        sa.CheckConstraint("reorder_point > 0", name="inventory_reorder_positive"))
    op.create_table("inventory_lot", identity(),
        reference("item_id", "inventory_item.id", nullable=False),
        sa.Column("code", sa.String(100), nullable=False),
        sa.UniqueConstraint("item_id", "code", name="inventory_lot_code_unique"))
    op.create_table("inventory_movement", identity(),
        reference("item_id", "inventory_item.id", nullable=False),
        reference("clinic_id", "reference_clinic.id", nullable=False),
        reference("lot_id", "inventory_lot.id"),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("delta", sa.BigInteger(), nullable=False),
        sa.Column("unit", sa.String(80), nullable=False),
        sa.Column("pack_label", sa.String(80)),
        sa.Column("pack_size", sa.BigInteger(), nullable=False),
        sa.Column("previous_quantity", sa.BigInteger(), nullable=False),
        sa.Column("counted_quantity", sa.BigInteger()),
        reference("correction_of", "inventory_movement.id", unique=True),
        sa.Column("reason", sa.String(500)),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("kind IN ('in', 'out', 'adjust', 'correction')", name="inventory_movement_kind"),
        sa.CheckConstraint("pack_size > 0", name="inventory_movement_pack_positive"),
        sa.CheckConstraint("(kind != 'in' OR delta > 0) AND (kind != 'out' OR delta < 0)", name="inventory_movement_sign"),
        sa.CheckConstraint("counted_quantity IS NULL OR counted_quantity >= 0", name="inventory_count_nonnegative"))
    op.create_index("ix_inventory_movement_scope_time", "inventory_movement", ["item_id", "clinic_id", "occurred_at", "id"])
    op.create_table("inventory_audit", identity(),
        reference("item_id", "inventory_item.id", nullable=False),
        reference("clinic_id", "reference_clinic.id"),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("action", sa.String(40), nullable=False),
        sa.Column("before_data", sa.JSON()), sa.Column("after_data", sa.JSON()),
        sa.Column("reason", sa.String(500)),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False))
    op.execute("""CREATE FUNCTION inventory_preserve_history() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'Inventory history is append-only'; END; $$""")
    for table in ("inventory_movement", "inventory_audit"):
        op.execute(f"CREATE TRIGGER {table}_immutable BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION inventory_preserve_history()")


def downgrade():
    # Explicit schema rollback destroys inventory history: backup/approval required.
    for table in ("inventory_audit", "inventory_movement", "inventory_lot", "inventory_clinic_item", "inventory_item"):
        op.drop_table(table)
    op.execute("DROP FUNCTION inventory_preserve_history()")
