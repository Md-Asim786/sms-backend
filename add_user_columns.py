from sqlalchemy import text
from app.core.database import engine

with engine.connect() as conn:
    # Check if columns exist
    result = conn.execute(
        text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name IN ('failed_login_attempts', 'locked_until', 'last_login')
    """)
    )
    existing = [row[0] for row in result]
    print("Existing columns:", existing)

    if "failed_login_attempts" not in existing:
        conn.execute(
            text("ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0")
        )
        conn.commit()
        print("Added failed_login_attempts")
    if "locked_until" not in existing:
        conn.execute(
            text("ALTER TABLE users ADD COLUMN locked_until TIMESTAMP WITH TIME ZONE")
        )
        conn.commit()
        print("Added locked_until")
    if "last_login" not in existing:
        conn.execute(
            text("ALTER TABLE users ADD COLUMN last_login TIMESTAMP WITH TIME ZONE")
        )
        conn.commit()
        print("Added last_login")
    print("Done!")
