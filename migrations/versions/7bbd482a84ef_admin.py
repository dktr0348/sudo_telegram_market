"""admin

Revision ID: 7bbd482a84ef
Revises: f743cc993291
Create Date: 2024-12-19 21:38:20.587930

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7bbd482a84ef"
down_revision: Union[str, None] = "f743cc993291"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
