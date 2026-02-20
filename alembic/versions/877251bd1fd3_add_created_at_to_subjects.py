"""add created_at to subjects

Revision ID: 877251bd1fd3
Revises: add_ay_st_tables
Create Date: 2026-02-20 11:12:42.956414

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '877251bd1fd3'
down_revision: Union[str, Sequence[str], None] = 'add_ay_st_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('subjects', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('subjects', 'created_at')

