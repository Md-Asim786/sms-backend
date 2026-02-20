"""Add group_id to student_applications and class_groups table

Revision ID: add_grp_id
Revises: add_academic_groups
Create Date: 2026-02-20

"""

from alembic import op
import sqlalchemy as sa
from uuid import uuid4

revision = "add_grp_id"
down_revision = "add_academic_groups"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add group_id to student_applications
    op.execute("""
        ALTER TABLE student_applications 
        ADD COLUMN IF NOT EXISTS group_id UUID REFERENCES academic_groups(id)
    """)

    # Create class_groups junction table
    op.execute("""
        CREATE TABLE IF NOT EXISTS class_groups (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            class_id UUID NOT NULL REFERENCES classes(id),
            group_id UUID NOT NULL REFERENCES academic_groups(id),
            UNIQUE(class_id, group_id)
        )
    """)

    # Remove deprecated columns from academic_groups (if they exist)
    op.execute("ALTER TABLE academic_groups DROP COLUMN IF EXISTS program_level")
    op.execute("ALTER TABLE academic_groups DROP COLUMN IF EXISTS start_class")
    op.execute("ALTER TABLE academic_groups DROP COLUMN IF EXISTS end_class")

    # Add group_id to teacher_subjects
    op.execute(
        "ALTER TABLE teacher_subjects ADD COLUMN IF NOT EXISTS group_id UUID REFERENCES academic_groups(id)"
    )

    # Create promotion_history table
    op.execute("""
        CREATE TABLE IF NOT EXISTS promotion_history (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            student_id UUID NOT NULL REFERENCES enrolled_students(id),
            from_class_id UUID NOT NULL REFERENCES classes(id),
            to_class_id UUID NOT NULL REFERENCES classes(id),
            from_section_id UUID REFERENCES sections(id),
            to_section_id UUID REFERENCES sections(id),
            from_group_id UUID REFERENCES academic_groups(id),
            to_group_id UUID REFERENCES academic_groups(id),
            from_academic_year_id UUID REFERENCES academic_years(id),
            to_academic_year_id UUID REFERENCES academic_years(id),
            exam_result VARCHAR(10) NOT NULL,
            promoted BOOLEAN DEFAULT TRUE,
            promoted_by UUID REFERENCES users(id),
            promoted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            is_undone BOOLEAN DEFAULT FALSE,
            undone_at TIMESTAMP WITH TIME ZONE,
            undone_by UUID REFERENCES users(id)
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS promotion_history")
    op.execute("ALTER TABLE teacher_subjects DROP COLUMN IF EXISTS group_id")
    op.execute("DROP TABLE IF EXISTS class_groups")
    op.execute("ALTER TABLE student_applications DROP COLUMN IF EXISTS group_id")
