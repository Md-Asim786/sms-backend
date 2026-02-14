"""remove school_name and logo_url from school_configs

Revision ID: 2b29d9e06e39
Revises: 5bbc182ca36b
Create Date: 2026-02-14 13:08:51.427369

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2b29d9e06e39"
down_revision: Union[str, Sequence[str], None] = "5bbc182ca36b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Remove school_name and logo_url columns from school_configs table
    op.drop_column("school_configs", "school_name")
    op.drop_column("school_configs", "logo_url")


def downgrade() -> None:
    """Downgrade schema."""
    # Add back school_name and logo_url columns
    op.add_column(
        "school_configs",
        sa.Column(
            "school_name", sa.String(), nullable=False, server_default="School Name"
        ),
    )
    op.add_column("school_configs", sa.Column("logo_url", sa.String(), nullable=True))
