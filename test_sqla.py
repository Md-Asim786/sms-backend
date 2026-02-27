
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.auth import User
from app.models.users import UserRole
import uuid

def test_insert():
    db = SessionLocal()
    try:
        print("Attempting to insert a test user...")
        test_email = f"test-{uuid.uuid4().hex[:6]}@example.com"
        user = User(
            email=test_email,
            password_hash="test_hash",
            role=UserRole.student,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Successfully inserted user: {user.id} with email {user.email}")
        
        # Verify columns
        print(f"User failed_login_attempts: {user.failed_login_attempts}")
        
        # Cleanup
        db.delete(user)
        db.commit()
        print("Test cleanup completed.")
        
    except Exception as e:
        print(f"Error during insertion: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_insert()
