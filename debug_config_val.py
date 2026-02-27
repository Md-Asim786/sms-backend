
from app.core.config import settings
from app.core.database import engine

def debug_config():
    print(f"Backend settings.DATABASE_URL: {settings.DATABASE_URL}")
    print(f"SQLAlchemy Engine URL: {engine.url}")

if __name__ == "__main__":
    debug_config()
