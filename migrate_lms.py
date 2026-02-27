"""
Database migration script to add new LMS columns
Run this script to update the database schema
"""
import sys
sys.path.insert(0, '.')

from sqlalchemy import text
from app.core.database import engine

def upgrade():
    with engine.connect() as conn:
        # Add new columns to assignments table
        try:
            conn.execute(text("""
                ALTER TABLE assignments 
                ADD COLUMN IF NOT EXISTS allow_reupload BOOLEAN DEFAULT TRUE,
                ADD COLUMN IF NOT EXISTS max_file_size_mb INTEGER DEFAULT 10,
                ADD COLUMN IF NOT EXISTS allowed_file_types JSON,
                ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE
            """))
            print("[OK] Added columns to assignments table")
        except Exception as e:
            print(f"Note: assignments table - {e}")
        
        conn.commit()
        
        # Add new column to assignment_submissions table
        try:
            conn.execute(text("""
                ALTER TABLE assignment_submissions 
                ADD COLUMN IF NOT EXISTS is_graded BOOLEAN DEFAULT FALSE
            """))
            print("[OK] Added is_graded column to assignment_submissions table")
        except Exception as e:
            print(f"Note: assignment_submissions table - {e}")
        
        conn.commit()
        
        # Add audit_logs column to attendance_records if not exists
        try:
            conn.execute(text("""
                ALTER TABLE attendance_records 
                ADD COLUMN IF NOT EXISTS audit_logs JSON
            """))
            print("[OK] Added audit_logs column to attendance_records table")
        except Exception as e:
            print(f"Note: attendance_records table - {e}")
        
        conn.commit()
        
    print("\n[SUCCESS] Database migration completed!")

def downgrade():
    with engine.connect() as conn:
        try:
            conn.execute(text("""
                ALTER TABLE assignments 
                DROP COLUMN IF EXISTS allow_reupload,
                DROP COLUMN IF EXISTS max_file_size_mb,
                DROP COLUMN IF EXISTS allowed_file_types,
                DROP COLUMN IF EXISTS updated_at
            """))
            print("[OK] Removed columns from assignments table")
        except Exception as e:
            print(f"Note: assignments table - {e}")
        
        conn.commit()
        
        try:
            conn.execute(text("""
                ALTER TABLE assignment_submissions 
                DROP COLUMN IF EXISTS is_graded
            """))
            print("[OK] Removed is_graded column from assignment_submissions table")
        except Exception as e:
            print(f"Note: assignment_submissions table - {e}")
        
        conn.commit()
        
        try:
            conn.execute(text("""
                ALTER TABLE attendance_records 
                DROP COLUMN IF EXISTS audit_logs
            """))
            print("[OK] Removed audit_logs column from attendance_records table")
        except Exception as e:
            print(f"Note: attendance_records table - {e}")
        
        conn.commit()
        
    print("\n[SUCCESS] Database rollback completed!")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--downgrade", action="store_true", help="Rollback migrations")
    args = parser.parse_args()
    
    if args.downgrade:
        downgrade()
    else:
        upgrade()
