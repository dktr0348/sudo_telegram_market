"""remove test column

Revision ID: 5d0a2ad702e7
Revises: 81b5742c0290
Create Date: 2023-12-21 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5d0a2ad702e7'
down_revision: Union[str, None] = '81b5742c0290'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('test_column')


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('test_column', sa.String(), nullable=True))
