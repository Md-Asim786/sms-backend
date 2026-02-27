
from sqlalchemy import text
from app.core.database import SessionLocal

def test_select():
    db = SessionLocal()
    try:
        print("Testing SELECT failed_login_attempts FROM users...")
        result = db.execute(text("SELECT failed_login_attempts FROM users LIMIT 1"))
        row = result.fetchone()
        print(f"Success! Result: {row}")
    except Exception as e:
        print(f"Select failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_select()
