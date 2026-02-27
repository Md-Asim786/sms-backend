
import psycopg2

DATABASE_URL = "postgresql://postgres@localhost:5432/sms_db"

def debug_db():
    print(f"Connecting to {DATABASE_URL}...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("\nColumns in 'public.users':")
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema='public' AND table_name='users'
            ORDER BY ordinal_position;
        """)
        for col in cur.fetchall():
            print(f"  - '{col[0]}'")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_db()
