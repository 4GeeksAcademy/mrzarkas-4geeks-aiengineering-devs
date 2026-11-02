"""Internal comparable threshold episodes; no backfill or business data changes."""
from alembic import op
import sqlalchemy as sa

revision = '0012_inventory_thresholds'
down_revision = '0011_inventory_audit_policy'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('inventory_threshold_state',
        sa.Column('item_id', sa.Uuid(), sa.ForeignKey('inventory_item.id'), primary_key=True),
        sa.Column('clinic_id', sa.Uuid(), sa.ForeignKey('reference_clinic.id'), primary_key=True),
        sa.Column('threshold', sa.BigInteger(), nullable=False),
        sa.Column('episode_id', sa.Uuid()),
        sa.CheckConstraint('threshold > 0', name='inventory_threshold_state_positive'))
    op.create_table('inventory_threshold_transition',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('episode_id', sa.Uuid(), nullable=False),
        sa.Column('movement_id', sa.Uuid(), sa.ForeignKey('inventory_movement.id'), nullable=False, unique=True),
        sa.Column('kind', sa.String(20), nullable=False),
        sa.Column('threshold', sa.BigInteger(), nullable=False),
        sa.Column('jurisdiction_id', sa.Uuid(), sa.ForeignKey('reference_jurisdiction.id'), nullable=False),
        sa.Column('jurisdiction_key', sa.String(100), nullable=False),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("kind IN ('activated', 'cleared')", name='inventory_threshold_transition_kind'),
        sa.CheckConstraint('threshold > 0', name='inventory_threshold_transition_positive'))
    op.create_index('ix_inventory_threshold_episode_time', 'inventory_threshold_transition', ['episode_id', 'occurred_at', 'id'])
    op.execute('CREATE TRIGGER inventory_threshold_transition_immutable BEFORE UPDATE OR DELETE ON inventory_threshold_transition FOR EACH ROW EXECUTE FUNCTION inventory_preserve_history()')


def downgrade():
    # Only explicitly authorized disposable schema procedures.
    op.drop_table('inventory_threshold_transition')
    op.drop_table('inventory_threshold_state')
