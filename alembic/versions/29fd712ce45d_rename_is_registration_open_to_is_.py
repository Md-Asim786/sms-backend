"""rename is_registration_open to is_admission_open

Revision ID: 29fd712ce45d
Revises: 2b29d9e06e39
Create Date: 2026-02-14 13:18:35.584753

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "29fd712ce45d"
down_revision: Union[str, Sequence[str], None] = "2b29d9e06e39"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename is_registration_open to is_admission_open
    op.alter_column(
        "school_configs", "is_registration_open", new_column_name="is_admission_open"
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Rename back
    op.alter_column(
        "school_configs", "is_admission_open", new_column_name="is_registration_open"
    )
