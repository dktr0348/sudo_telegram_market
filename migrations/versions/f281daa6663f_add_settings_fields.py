"""add settings fields

Revision ID: f281daa6663f
Revises: 
Create Date: 2024-01-02

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'f281daa6663f'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Используем batch режим для SQLite
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('language', sa.String(), server_default='ru', nullable=False))
        batch_op.add_column(sa.Column('notifications', sa.Boolean(), server_default='1', nullable=False))

def downgrade() -> None:
    # Используем batch режим для SQLite
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('notifications')
        batch_op.drop_column('language')
