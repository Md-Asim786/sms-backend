from datetime import datetime, timedelta
from typing import Any, Union, Optional
from jose import jwt
import bcrypt
import re
from app.core.config import settings

ALGORITHM = settings.ALGORITHM
SECRET_KEY = settings.SECRET_KEY


def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(12)).decode("utf-8")


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input to prevent XSS and injection attacks"""
    if not text:
        return ""
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    # Truncate to max length
    if len(text) > max_length:
        text = text[:max_length]
    
    # HTML escape common XSS vectors
    dangerous_patterns = [
        (r'<script[^>]*>', ''),
        (r'javascript:', ''),
        (r'on\w+\s*=', ''),
        (r'<iframe[^>]*>', ''),
        (r'<object[^>]*>', ''),
        (r'<embed[^>]*>', ''),
    ]
    
    for pattern, replacement in dangerous_patterns:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    return text


def validate_file_extension(filename: str, allowed_extensions: list) -> bool:
    """Validate file extension to prevent malicious uploads"""
    if not filename:
        return False
    
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    return ext in [e.lower().lstrip('.') for e in allowed_extensions]


def generate_secure_filename(original_filename: str) -> str:
    """Generate a secure random filename while preserving extension"""
    import uuid
    
    if not original_filename:
        return str(uuid.uuid4())
    
    # Get the extension
    parts = original_filename.rsplit('.', 1)
    ext = parts[-1].lower() if len(parts) > 1 else ''
    
    # Generate UUID-based filename
    secure_name = str(uuid.uuid4())
    
    return f"{secure_name}.{ext}" if ext else secure_name
