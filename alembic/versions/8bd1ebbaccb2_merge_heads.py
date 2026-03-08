"""merge heads

Revision ID: 8bd1ebbaccb2
Revises: 2b892244d0af, 8c9d2f6f3f2a
Create Date: 2026-03-08 14:04:48.591187

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8bd1ebbaccb2'
down_revision: Union[str, Sequence[str], None] = ('2b892244d0af', '8c9d2f6f3f2a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
