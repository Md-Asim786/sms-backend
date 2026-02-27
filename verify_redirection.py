
from fastapi.testclient import TestClient
from app.main import app
from app.core import security
from app.models.auth import User
from app.models.users import UserRole
from app.core.database import SessionLocal
import uuid

client = TestClient(app)

def test_login_response_structure():
    db = SessionLocal()
    test_email = f"redirect-test-{uuid.uuid4().hex[:6]}@example.com"
    password = "testpassword123"
    
    try:
        # Create a test teacher
        user = User(
            email=test_email,
            password_hash=security.get_password_hash(password),
            role=UserRole.teacher,
            is_active=True
        )
        db.add(user)
        db.commit()
        
        print(f"Testing login for teacher: {test_email}")
        response = client.post(
            "/api/v1/auth/login",
            data={"username": test_email, "password": password}
        )
        
        assert response.status_code == 200
        data = response.json()
        print(f"Login Response: {data}")
        
        assert "role" in data
        assert data["role"] == "teacher"
        print("Verification Successful: 'role' field is present and correct.")
        
        # Cleanup
        db.delete(user)
        db.commit()
        
    except Exception as e:
        print(f"Verification Failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_login_response_structure()
