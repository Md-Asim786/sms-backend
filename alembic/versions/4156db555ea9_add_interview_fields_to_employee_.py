"""add interview fields to employee_applications

Revision ID: 4156db555ea9
Revises: fdc2d3bec3f7
Create Date: 2026-02-14 15:21:34.993875

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4156db555ea9"
down_revision: Union[str, Sequence[str], None] = "fdc2d3bec3f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "employee_applications", sa.Column("interview_date", sa.String(), nullable=True)
    )
    op.add_column(
        "employee_applications", sa.Column("interview_time", sa.String(), nullable=True)
    )
    op.add_column(
        "employee_applications",
        sa.Column("interview_location", sa.String(), nullable=True),
    )
    op.add_column(
        "employee_applications", sa.Column("interview_notes", sa.Text(), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("employee_applications", "interview_notes")
    op.drop_column("employee_applications", "interview_location")
    op.drop_column("employee_applications", "interview_time")
    op.drop_column("employee_applications", "interview_date")
