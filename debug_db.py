
import psycopg2

DATABASE_URL = "postgresql://postgres@localhost:5432/sms_db"

def debug_db():
    print(f"Connecting to {DATABASE_URL}...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name='users'
            ORDER BY ordinal_position;
        """)
        
        columns = cur.fetchall()
        print(f"Columns in 'users' table:")
        for col in columns:
            print(f"  - {col[0]} ({col[1]})")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_db()
