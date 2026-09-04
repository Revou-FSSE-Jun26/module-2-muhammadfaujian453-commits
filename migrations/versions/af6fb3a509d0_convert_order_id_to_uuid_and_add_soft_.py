"""convert order id to uuid and add soft delete

Revision ID: af6fb3a509d0
Revises: 03f0ece28a3d
Create Date: 2026-09-04 20:26:55.290072

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'af6fb3a509d0'
down_revision = '03f0ece28a3d'
branch_labels = None
depends_on = None


def upgrade():
    # --- Soft delete flag (independen dari perubahan UUID) ---
    op.add_column('orders', sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()))

    # --- UUID surgery ---
    op.add_column('orders', sa.Column('id_uuid', sa.Uuid(), nullable=False, server_default=sa.text('gen_random_uuid()')))
    op.add_column('order_items', sa.Column('order_id_uuid', sa.Uuid(), nullable=True))

    op.execute("""
        UPDATE order_items
        SET order_id_uuid = orders.id_uuid
        FROM orders
        WHERE order_items.order_id = orders.id
    """)

    op.alter_column('order_items', 'order_id_uuid', nullable=False)

    op.drop_constraint('order_items_pkey', 'order_items', type_='primary')
    op.drop_constraint('order_items_order_id_fkey', 'order_items', type_='foreignkey')
    op.drop_column('order_items', 'order_id')
    op.alter_column('order_items', 'order_id_uuid', new_column_name='order_id')

    op.drop_constraint('orders_pkey', 'orders', type_='primary')
    op.drop_column('orders', 'id')
    op.alter_column('orders', 'id_uuid', new_column_name='id', server_default=None)

    op.create_primary_key('orders_pkey', 'orders', ['id'])
    op.create_primary_key('order_items_pkey', 'order_items', ['order_id', 'product_id'])
    op.create_foreign_key('order_items_order_id_fkey', 'order_items', 'orders', ['order_id'], ['id'], ondelete='CASCADE')



def downgrade():
    raise NotImplementedError("This migration is not reversible — order IDs cannot be safely converted back to sequential integers once UUIDs are assigned.")
