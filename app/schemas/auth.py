from typing import Optional, List
from pydantic import BaseModel


class Token(BaseModel):
    success: bool = True
    message: str = "Success"
    data: dict
    # Legacy fields for OAuth2 compatibility if needed by other clients
    access_token: Optional[str] = None
    token_type: Optional[str] = None


class TokenPayload(BaseModel):
    sub: Optional[str] = None


class Login(BaseModel):
    email: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: str


class PasswordResetVerify(BaseModel):
    email: str
    otp_code: str


class PasswordResetConfirm(BaseModel):
    email: str
    otp_code: str
    new_password: str


class StudentProfile(BaseModel):
    id: str
    name: str
    class_name: str
    roll_number: Optional[str] = None


class DuplicateEmailResponse(BaseModel):
    message: str
    students: List[StudentProfile]
