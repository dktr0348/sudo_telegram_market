"""restore_user_profile

Revision ID: 466633f4ed27
Revises: 1d69bd11fd11
Create Date: 2024-12-22 21:05:21.812069

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "466633f4ed27"
down_revision: Union[str, None] = "1d69bd11fd11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "user_profiles",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("phone_number", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("location_lat", sa.Float(), nullable=True),
        sa.Column("location_lon", sa.Float(), nullable=True),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("photo_id", sa.String(), nullable=True),
        sa.Column("reg_date", sa.DateTime(), nullable=True),
        sa.Column("is_admin", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.user_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("user_id"),
    )
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("location_lat")
        batch_op.drop_column("email")
        batch_op.drop_column("location_lon")
        batch_op.drop_column("phone")
        batch_op.drop_column("photo_id")
        batch_op.drop_column("age")

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("age", sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column("photo_id", sa.VARCHAR(), nullable=True))
        batch_op.add_column(sa.Column("phone", sa.VARCHAR(), nullable=True))
        batch_op.add_column(
            sa.Column("location_lon", sa.FLOAT(), nullable=True)
        )
        batch_op.add_column(sa.Column("email", sa.VARCHAR(), nullable=True))
        batch_op.add_column(
            sa.Column("location_lat", sa.FLOAT(), nullable=True)
        )

    op.drop_table("user_profiles")
    # ### end Alembic commands ###