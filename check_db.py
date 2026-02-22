import os
import sys
from sqlalchemy import create_engine, inspect

# Add the current directory to sys.path to import app
sys.path.append(os.getcwd())

from app.core.config import settings

def check_columns():
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)
    columns = inspector.get_columns('employee_applications')
    print("--- START ---")
    for column in columns:
        print(f"COLUMN_NAME: {column['name']}")
    print("--- END ---")

if __name__ == "__main__":
    check_columns()
