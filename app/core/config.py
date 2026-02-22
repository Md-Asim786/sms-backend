import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "School Admin Portal API"
    API_V1_STR: str = "/api/v1"
    
    # Database
    #DATABASE_URL: str = "postgresql://postgres:asim1234@localhost:5432/sms_db"
    DATABASE_URL: str = "postgresql://postgres@localhost:5432/sms_db"
    
    SCHOOL_NAME_ABBR: str = "PAEC"
    UPLOAD_DIR: str = "uploads"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
