
import psycopg2

DATABASE_URL = "postgresql://postgres@localhost:5432/sms_db"

def debug_db():
    print(f"Connecting to {DATABASE_URL}...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("Listing ALL tables named 'users' in ALL schemas:")
        cur.execute("""
            SELECT table_schema, table_name 
            FROM information_schema.tables 
            WHERE table_name='users';
        """)
        tables = cur.fetchall()
        for table in tables:
            schema = table[0]
            print(f"  - Schema: {schema}")
            
            # Check columns in this specific schema
            cur.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema='{schema}' AND table_name='users' AND column_name='failed_login_attempts';
            """)
            has_col = cur.fetchone() is not None
            print(f"    Has 'failed_login_attempts' column: {has_col}")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_db()
