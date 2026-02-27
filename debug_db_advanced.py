
import psycopg2

DATABASE_URL = "postgresql://postgres@localhost:5432/sms_db"

def debug_db():
    print(f"Connecting to {DATABASE_URL}...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("Checking for 'users' tables across all schemas:")
        cur.execute("""
            SELECT table_schema, table_name 
            FROM information_schema.tables 
            WHERE table_name='users';
        """)
        tables = cur.fetchall()
        for table in tables:
            print(f"  - Schema: {table[0]}, Table: {table[1]}")
            
        print("\nChecking search_path:")
        cur.execute("SHOW search_path;")
        print(f"  search_path: {cur.fetchone()[0]}")

        print("\nChecking current database:")
        cur.execute("SELECT current_database();")
        print(f"  current_database: {cur.fetchone()[0]}")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_db()
