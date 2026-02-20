"""add academic year student teacher subject tables

Revision ID: add_ay_st_tables
Revises: fdc2d3bec3f7, 4156db555ea9
Create Date: 2026-02-20

"""

from alembic import op
import sqlalchemy as sa

revision = "add_ay_st_tables"
down_revision = ("fdc2d3bec3f7", "4156db555ea9")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'subjecttype') THEN
                CREATE TYPE subjecttype AS ENUM ('compulsory', 'elective');
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'studentsubjectstatus') THEN
                CREATE TYPE studentsubjectstatus AS ENUM ('active', 'dropped');
            END IF;
        END $$;
    """)

    # Create academic_years table
    op.execute("""
        CREATE TABLE academic_years (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR NOT NULL,
            start_year INTEGER NOT NULL,
            end_year INTEGER NOT NULL,
            is_current BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)

    # Add grade_level and academic_year_id to classes table
    op.add_column("classes", sa.Column("grade_level", sa.Integer(), nullable=True))
    op.add_column("classes", sa.Column("academic_year_id", sa.UUID(), nullable=True))
    op.execute(
        "ALTER TABLE classes ADD CONSTRAINT classes_academic_year_fk FOREIGN KEY (academic_year_id) REFERENCES academic_years(id)"
    )

    # Add type to subjects table
    op.execute("ALTER TABLE subjects ADD COLUMN type subjecttype DEFAULT 'compulsory'")

    # Add academic_year_id and periods_per_week to class_subjects
    op.add_column(
        "class_subjects", sa.Column("academic_year_id", sa.UUID(), nullable=True)
    )
    op.add_column(
        "class_subjects",
        sa.Column("periods_per_week", sa.Integer(), nullable=True, server_default="1"),
    )
    op.execute(
        "ALTER TABLE class_subjects ADD CONSTRAINT class_subjects_academic_year_fk FOREIGN KEY (academic_year_id) REFERENCES academic_years(id)"
    )

    # Remove teacher_id from class_subjects
    op.drop_column("class_subjects", "teacher_id")

    # Create student_subjects table
    op.execute("""
        CREATE TABLE student_subjects (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            student_id UUID NOT NULL REFERENCES enrolled_students(id),
            class_id UUID NOT NULL REFERENCES classes(id),
            subject_id UUID NOT NULL REFERENCES subjects(id),
            class_subject_id UUID NOT NULL REFERENCES class_subjects(id),
            academic_year_id UUID REFERENCES academic_years(id),
            status studentsubjectstatus DEFAULT 'active',
            enrolled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)

    # Create teacher_subjects table
    op.execute("""
        CREATE TABLE teacher_subjects (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            teacher_id UUID NOT NULL REFERENCES enrolled_employees(id),
            class_id UUID NOT NULL REFERENCES classes(id),
            section_id UUID REFERENCES sections(id),
            subject_id UUID NOT NULL REFERENCES subjects(id),
            class_subject_id UUID NOT NULL REFERENCES class_subjects(id),
            academic_year_id UUID REFERENCES academic_years(id),
            assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE teacher_subjects")
    op.execute("DROP TABLE student_subjects")

    op.execute(
        "ALTER TABLE class_subjects DROP CONSTRAINT class_subjects_academic_year_fk"
    )
    op.execute("ALTER TABLE class_subjects DROP COLUMN academic_year_id")
    op.execute("ALTER TABLE class_subjects DROP COLUMN periods_per_week")

    op.execute("ALTER TABLE class_subjects ADD COLUMN teacher_id UUID")

    op.execute("ALTER TABLE subjects DROP COLUMN type")

    op.execute("ALTER TABLE classes DROP CONSTRAINT classes_academic_year_fk")
    op.execute("ALTER TABLE classes DROP COLUMN academic_year_id")
    op.execute("ALTER TABLE classes DROP COLUMN grade_level")

    op.execute("DROP TABLE academic_years")
    op.execute("DROP TYPE studentsubjectstatus")
    op.execute("DROP TYPE subjecttype")
