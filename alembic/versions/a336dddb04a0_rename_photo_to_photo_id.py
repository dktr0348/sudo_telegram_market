"""rename_photo_to_photo_id

Revision ID: a336dddb04a0
Revises: 466633f4ed27
Create Date: 2024-12-22 21:14:23.710172

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a336dddb04a0"
down_revision: Union[str, None] = "466633f4ed27"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("products", schema=None) as batch_op:
        batch_op.add_column(sa.Column("photo_id", sa.String(), nullable=True))
        batch_op.drop_column("photo")

    with op.batch_alter_table("user_profiles", schema=None) as batch_op:
        batch_op.drop_column("reg_date")
        batch_op.drop_column("is_admin")

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("user_profiles", schema=None) as batch_op:
        batch_op.add_column(sa.Column("is_admin", sa.BOOLEAN(), nullable=True))
        batch_op.add_column(
            sa.Column("reg_date", sa.DATETIME(), nullable=True)
        )

    with op.batch_alter_table("products", schema=None) as batch_op:
        batch_op.add_column(sa.Column("photo", sa.VARCHAR(), nullable=True))
        batch_op.drop_column("photo_id")

    # ### end Alembic commands ###
