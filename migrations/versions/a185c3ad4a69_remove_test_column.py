"""remove_test_column

Revision ID: a185c3ad4a69
Revises: 9c8619b314eb
Create Date: 2024-12-21 16:50:52.104712

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a185c3ad4a69"
down_revision: Union[str, None] = "9c8619b314eb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("test")

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("test", sa.VARCHAR(), nullable=True))

    # ### end Alembic commands ###