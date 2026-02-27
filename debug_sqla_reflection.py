
from sqlalchemy import inspect
from app.core.database import engine

def debug_sqla():
    print(f"Engine URL: {engine.url}")
    inspector = inspect(engine)
    
    print("\nTables found by SQLAlchemy:")
    tables = inspector.get_table_names()
    print(f"  {tables}")
    
    if 'users' in tables:
        print("\nColumns in 'users' (via SQLAlchemy Inspector):")
        columns = inspector.get_columns('users')
        for col in columns:
            print(f"  - {col['name']} ({col['type']})")
    else:
        print("\n'users' table NOT found by SQLAlchemy!")

if __name__ == "__main__":
    debug_sqla()
