"""add academic groups and student group enrollment

Revision ID: add_academic_groups
Revises: add_ay_st_tables
Create Date: 2026-02-20

"""

from alembic import op
import sqlalchemy as sa

revision = "add_academic_groups"
down_revision = ("add_ay_st_tables", "877251bd1fd3")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'programlevel') THEN
                CREATE TYPE programlevel AS ENUM ('matric', 'intermediate');
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'subjectsourcetype') THEN
                CREATE TYPE subjectsourcetype AS ENUM ('group', 'manual');
            END IF;
        END $$;
    """)

    # Create academic_groups table
    op.execute("""
        CREATE TABLE academic_groups (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR NOT NULL,
            code VARCHAR UNIQUE NOT NULL,
            description TEXT,
            program_level programlevel NOT NULL,
            start_class INTEGER NOT NULL,
            end_class INTEGER NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)

    # Create group_subjects table
    op.execute("""
        CREATE TABLE group_subjects (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            group_id UUID NOT NULL REFERENCES academic_groups(id),
            subject_id UUID NOT NULL REFERENCES subjects(id),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(group_id, subject_id)
        )
    """)

    # Create student_group_enrollments table
    op.execute("""
        CREATE TABLE student_group_enrollments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            student_id UUID NOT NULL REFERENCES enrolled_students(id),
            group_id UUID NOT NULL REFERENCES academic_groups(id),
            academic_year_id UUID REFERENCES academic_years(id),
            is_locked BOOLEAN DEFAULT FALSE,
            enrolled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)

    # Add source_type to student_subjects
    op.execute(
        "ALTER TABLE student_subjects ADD COLUMN source_type subjectsourcetype DEFAULT 'manual'"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE student_subjects DROP COLUMN source_type")
    op.execute("DROP TABLE student_group_enrollments")
    op.execute("DROP TABLE group_subjects")
    op.execute("DROP TABLE academic_groups")
    op.execute("DROP TYPE subjectsourcetype")
    op.execute("DROP TYPE programlevel")
