
import psycopg2
from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL

def verify():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # 1. Check Tables
        print("Checking tables...")
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
        tables = [t[0] for t in cur.fetchall()]
        print(f"Tables found: {tables}")
        
        required_tables = ['users', 'user_sessions', 'password_reset_otps']
        for table in required_tables:
            if table in tables:
                print(f"Table '{table}' exists.")
                # 2. Check Columns for 'users'
                if table == 'users':
                    cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}';")
                    cols = [c[0] for c in cur.fetchall()]
                    print(f"Columns in 'users': {cols}")
                    required_cols = ['failed_login_attempts', 'locked_until', 'last_login']
                    for col in required_cols:
                        if col in cols:
                            print(f"  Column '{col}' exists.")
                        else:
                            print(f"  CRITICAL: Column '{col}' MISSING in 'users'!")
            else:
                print(f"CRITICAL: Table '{table}' MISSING!")
                
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify()
