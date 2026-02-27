
import psycopg2

DATABASE_URL = "postgresql://postgres@localhost:5432/sms_db"

def debug_db():
    print(f"Connecting to {DATABASE_URL}...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("\nListing all schemas:")
        cur.execute("SELECT schema_name FROM information_schema.schemata;")
        for schema in cur.fetchall():
            print(f"  - {schema[0]}")
            
        print("\nChecking for 'users' tables in ALL schemas:")
        cur.execute("""
            SELECT table_schema, table_name 
            FROM information_schema.tables 
            WHERE table_name='users';
        """)
        for table in cur.fetchall():
            print(f"  - Schema: {table[0]}, Table: {table[1]}")
            
            # Count columns in this specific schema's table
            cur.execute(f"SELECT count(*) FROM information_schema.columns WHERE table_schema='{table[0]}' AND table_name='users';")
            col_count = cur.fetchone()[0]
            print(f"    Columns: {col_count}")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_db()
