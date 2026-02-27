
import psycopg2
from sqlalchemy import create_engine, text
from app.core.config import settings

DATABASE_URL = "postgresql://postgres@localhost:5432/sms_db"

def test_raw_psycopg2():
    print("\n--- Testing Raw Psycopg2 Insert ---")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (id, email, password_hash, role, is_active, failed_login_attempts)
            VALUES (gen_random_uuid(), 'raw@test.com', 'hash', 'student', true, 0)
            RETURNING id;
        """)
        new_id = cur.fetchone()[0]
        print(f"Success! Inserted raw ID: {new_id}")
        conn.rollback() # Don't actually keep it
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Raw Psycopg2 Failed: {e}")

def test_raw_sqlalchemy():
    print("\n--- Testing Raw SQLAlchemy Text Insert ---")
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO users (id, email, password_hash, role, is_active, failed_login_attempts)
                VALUES (gen_random_uuid(), 'sqla_raw@test.com', 'hash', 'student', true, 0)
            """))
            conn.commit()
            print("Success! Inserted via raw SQLAlchemy text.")
            # Cleanup
            conn.execute(text("DELETE FROM users WHERE email='sqla_raw@test.com'"))
            conn.commit()
    except Exception as e:
        print(f"Raw SQLAlchemy Failed: {e}")

if __name__ == "__main__":
    test_raw_psycopg2()
    test_raw_sqlalchemy()
