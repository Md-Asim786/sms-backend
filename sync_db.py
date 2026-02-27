
import psycopg2
from app.core.config import settings

# Database connection URL from settings
DATABASE_URL = settings.DATABASE_URL

def sync_db():
    print(f"Connecting to database...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # 1. Ensure extensions exist
        print("Ensuring uuid-ossp extension exists...")
        cur.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

        # 2. Sync 'users' table columns
        print("Checking 'users' table columns...")
        users_columns = [
            ("failed_login_attempts", "INTEGER DEFAULT 0"),
            ("locked_until", "TIMESTAMP WITH TIME ZONE"),
            ("last_login", "TIMESTAMP WITH TIME ZONE")
        ]
        
        for col_name, col_def in users_columns:
            cur.execute(f"""
                SELECT count(*) 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='{col_name}';
            """)
            if cur.fetchone()[0] == 0:
                print(f"  Adding column {col_name} to users table...")
                cur.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def};")
            else:
                print(f"  Column {col_name} already exists.")

        # 3. Create missing tables
        print("Creating missing tables...")
        
        # user_sessions table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                refresh_token VARCHAR UNIQUE NOT NULL,
                user_agent TEXT,
                ip_address VARCHAR,
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("  Table 'user_sessions' ensured.")

        # password_reset_otps table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS password_reset_otps (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                email VARCHAR NOT NULL,
                otp_code VARCHAR(6) NOT NULL,
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                is_used BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("  Table 'password_reset_otps' ensured.")

        # 4. Sync enrolled_students and enrolled_employees
        print("Checking enrolled_students and enrolled_employees columns...")
        extra_columns = {
            "enrolled_students": [
                ("lms_password", "TEXT"),
                ("user_id", "UUID REFERENCES users(id)"),
                ("group_id", "UUID REFERENCES academic_groups(id) NULL")
            ],
            "enrolled_employees": [
                ("lms_password", "TEXT"),
                ("user_id", "UUID REFERENCES users(id)")
            ]
        }

        for table, cols in extra_columns.items():
            for col_name, col_def in cols:
                cur.execute(f"""
                    SELECT count(*) 
                    FROM information_schema.columns 
                    WHERE table_name='{table}' AND column_name='{col_name}';
                """)
                if cur.fetchone()[0] == 0:
                    print(f"  Adding column {col_name} to {table} table...")
                    try:
                        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def};")
                    except Exception as e:
                        print(f"  Warning: Could not add column {col_name} to {table}: {e}")
                        conn.rollback() # Rollback the failure
                        cur = conn.cursor() # Get new cursor
                else:
                    print(f"  Column {col_name} exists in {table}.")

        conn.commit()
        print("Database sync completed successfully.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error syncing database: {e}")

if __name__ == "__main__":
    sync_db()
