
import psycopg2
from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL

def debug_tables():
    print(f"Connecting to database...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema='public'
            ORDER BY table_name;
        """)
        
        tables = cur.fetchall()
        print(f"Tables found in 'public' schema:")
        for table in tables:
            tname = table[0]
            print(f"  - {tname}")
            # Optional: list columns for key tables
            if tname in ['users', 'user_sessions', 'enrolled_students', 'enrolled_employees', 'password_reset_otps']:
                cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='{tname}';")
                cols = [c[0] for c in cur.fetchall()]
                print(f"    Columns: {', '.join(cols)}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_tables()
