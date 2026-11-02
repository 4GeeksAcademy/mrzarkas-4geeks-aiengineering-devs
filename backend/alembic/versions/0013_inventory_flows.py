"""Internal flow lifecycle; no backfill or existing table changes."""
from alembic import op
import sqlalchemy as sa
revision = '0013_inventory_flows'
down_revision = '0012_inventory_thresholds'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('inventory_telemetry_flow',
        sa.Column('flow_id', sa.String(67), primary_key=True),
        sa.Column('actor_id', sa.Uuid(), nullable=False),
        sa.Column('item_id', sa.Uuid(), sa.ForeignKey('inventory_item.id'), nullable=False),
        sa.Column('clinic_id', sa.Uuid(), sa.ForeignKey('reference_clinic.id'), nullable=False),
        sa.Column('jurisdiction_id', sa.Uuid(), sa.ForeignKey('reference_jurisdiction.id'), nullable=False),
        sa.Column('jurisdiction_key', sa.String(100), nullable=False),
        sa.Column('environment', sa.String(20), nullable=False),
        sa.Column('key_version', sa.String(100), nullable=False),
        sa.Column('direction', sa.String(20)),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_step', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('closed_at', sa.DateTime(timezone=True)),
        sa.CheckConstraint("status IN ('open','completed','abandoned','uncertain')", name='inventory_flow_status'),
        sa.CheckConstraint("last_step IN ('selection','validation','confirmation')", name='inventory_flow_step'),
        sa.CheckConstraint("direction IS NULL OR direction IN ('inbound','outbound')", name='inventory_flow_direction'))
    op.create_index('ix_inventory_flow_due', 'inventory_telemetry_flow', ['status','last_activity_at','flow_id'])


def downgrade():
    op.drop_table('inventory_telemetry_flow')
