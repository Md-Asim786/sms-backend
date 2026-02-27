"""add_assignment_attachment_fields

Revision ID: 8c9d2f6f3f2a
Revises: b5a01fb7de90
Create Date: 2026-02-26 20:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "8c9d2f6f3f2a"
down_revision: Union[str, Sequence[str], None] = "b5a01fb7de90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_cols = {col["name"] for col in inspector.get_columns("assignments")}

    if "attachments" not in existing_cols:
        op.add_column("assignments", sa.Column("attachments", sa.JSON(), nullable=True))
    if "allow_reupload" not in existing_cols:
        op.add_column(
            "assignments",
            sa.Column("allow_reupload", sa.Boolean(), nullable=True, server_default=sa.text("true")),
        )
    if "max_file_size_mb" not in existing_cols:
        op.add_column(
            "assignments",
            sa.Column("max_file_size_mb", sa.Integer(), nullable=True, server_default=sa.text("10")),
        )
    if "allowed_file_types" not in existing_cols:
        op.add_column("assignments", sa.Column("allowed_file_types", sa.JSON(), nullable=True))
    if "updated_at" not in existing_cols:
        op.add_column("assignments", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("assignments", "updated_at")
    op.drop_column("assignments", "allowed_file_types")
    op.drop_column("assignments", "max_file_size_mb")
    op.drop_column("assignments", "allow_reupload")
    op.drop_column("assignments", "attachments")
