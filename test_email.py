import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.email import send_reset_password_email
from app.core.config import settings

def test_email_sending():
    test_email = settings.EMAILS_FROM_EMAIL
    print(f"Testing email sending to: {test_email}")
    
    result = send_reset_password_email(test_email, "123456")
    
    if result:
        print("SUCCESS: Email sent successfully!")
    else:
        print("FAILED: Email could not be sent. Check your SMTP settings and credentials.")

if __name__ == "__main__":
    test_email_sending()
