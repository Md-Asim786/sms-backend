import os
from pydantic_settings import BaseSettings
from typing import List, Optional, Any

class Settings(BaseSettings):
    PROJECT_NAME: str = "School Admin Portal API"
    API_V1_STR: str = "/api/v1"
    
    # Database
    #DATABASE_URL: str = "postgresql://postgres:asim1234@localhost:5432/sms_db"
    DATABASE_URL: str = "postgresql://postgres@localhost:5432/sms_db"
    
    SCHOOL_NAME_ABBR: str = "PAEC"
    UPLOAD_DIR: str = "uploads"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "SECRET_KEY_CHANGE_ME_IN_PRODUCTION")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # SMTP Settings (Use environment variables)
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = os.getenv("SMTP_PORT")
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST")
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    EMAILS_FROM_EMAIL: Optional[str] = os.getenv("EMAILS_FROM_EMAIL")
    EMAILS_FROM_NAME: Optional[str] = os.getenv("EMAILS_FROM_NAME")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"

settings = Settings()
