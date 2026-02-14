"""add admission_deadline to school_configs

Revision ID: fdc2d3bec3f7
Revises: 29fd712ce45d
Create Date: 2026-02-14 13:19:59.863277

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "fdc2d3bec3f7"
down_revision: Union[str, Sequence[str], None] = "29fd712ce45d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add admission_deadline column
    op.add_column(
        "school_configs", sa.Column("admission_deadline", sa.String(), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop admission_deadline column
    op.drop_column("school_configs", "admission_deadline")
