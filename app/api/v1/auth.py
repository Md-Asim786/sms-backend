from datetime import datetime, timedelta
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Body, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.auth import User, UserSession
from app.models.users import EnrolledStudent, EnrolledEmployee
from app.schemas.auth import Token, Login, RefreshTokenRequest
from app.utils.audit_logger import audit_logger

router = APIRouter()


def authenticate_user(
    db: Session, email_or_login: str, password: str
) -> Optional[User]:
    print(f"Authenticating: {email_or_login}")

    # 1. Check User table (Centralized auth)
    user = db.query(User).filter(User.email == email_or_login).first()
    print(f"User from email query: {user}")

    # 2. If not found, check LMS credentials in EnrolledStudent
    if not user:
        student = (
            db.query(EnrolledStudent)
            .filter(
                (EnrolledStudent.lms_email == email_or_login)
                | (EnrolledStudent.lms_login == email_or_login)
            )
            .first()
        )
        print(f"Student found: {student}")
        if student and student.user_id:
            user = db.query(User).filter(User.id == student.user_id).first()

    # 3. Check EnrolledEmployee (Teachers/Staff)
    if not user:
        employee = (
            db.query(EnrolledEmployee)
            .filter(
                (EnrolledEmployee.lms_email == email_or_login)
                | (EnrolledEmployee.lms_login == email_or_login)
            )
            .first()
        )
        print(f"Employee found: {employee}")
        if employee and employee.user_id:
            user = db.query(User).filter(User.id == employee.user_id).first()

    if not user:
        print("No user found")
        return None

    print(f"Found user: {user.email}, verifying password")

    # Simple password check
    if not security.verify_password(password, user.password_hash):
        print("Password mismatch")
        return None

    print("Password verified, returning user")
    return user


@router.post("/login")
def login_access_token(
    response: Response,
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    print(f"\n=== LOGIN DEBUG ===")
    print(f"Username: {form_data.username}")
    print(f"==================\n")

    user = authenticate_user(db, form_data.username, form_data.password)
    print(f"User after authenticate: {user}")

    if not user:
        # Log failed login attempt
        audit_logger.log_login(
            user_id="unknown", email=form_data.username, role="unknown", success=False
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "message": "Invalid email or password",
                "data": None,
            },
        )

    # Check is_active
    is_active = getattr(user, "is_active", True)
    if is_active == False:
        audit_logger.log_login(
            user_id=str(user.id),
            email=user.email,
            role=user.role.value if hasattr(user.role, "value") else str(user.role),
            success=False,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"success": False, "message": "Account is inactive", "data": None},
        )

    access_token = security.create_access_token(str(user.id))
    refresh_token = security.create_refresh_token(str(user.id))

    # Store refresh token in session
    session = UserSession(
        user_id=user.id,
        refresh_token=refresh_token,
        expires_at=datetime.utcnow()
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(session)
    db.commit()

    # Set HTTP-only cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
    )

    # Determine redirect based on role
    user_role = user.role.value if hasattr(user.role, "value") else user.role
    if user_role == "teacher":
        redirect_to = "/lms/teacher/dashboard"
    elif user_role == "student":
        redirect_to = "/lms/student/dashboard"
    elif user_role == "admin":
        redirect_to = "/lms/teacher/dashboard"
    else:
        redirect_to = "/"

    # Try to derive a display name from linked student/employee records
    display_name = user.email
    student_profile = (
        db.query(EnrolledStudent).filter(EnrolledStudent.user_id == user.id).first()
    )
    if student_profile:
        display_name = (
            f"{student_profile.first_name} {student_profile.last_name}".strip()
        )
    else:
        employee_profile = (
            db.query(EnrolledEmployee)
            .filter(EnrolledEmployee.user_id == user.id)
            .first()
        )
        if employee_profile:
            display_name = (
                f"{employee_profile.first_name} {employee_profile.last_name}".strip()
            )

    print(f"Login SUCCESS for: {user.email}, role: {user_role}")

    # Log successful login
    audit_logger.log_login(
        user_id=str(user.id), email=user.email, role=user_role, success=True
    )

    return {
        "success": True,
        "message": "Login successful",
        "data": {
            "token": access_token,
            "role": user_role,
            "redirect_to": redirect_to,
            "name": display_name,
            "email": user.email,
        },
    }


@router.post("/refresh", response_model=Token)
def refresh_token(
    response: Response,
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Refresh access token using refresh token
    """
    session = (
        db.query(UserSession)
        .filter(
            UserSession.refresh_token == refresh_data.refresh_token,
            UserSession.expires_at > datetime.utcnow(),
        )
        .first()
    )

    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    new_access_token = security.create_access_token(str(session.user_id))

    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    user = db.query(User).filter(User.id == session.user_id).first()

    return {
        "access_token": new_access_token,
        "refresh_token": session.refresh_token,
        "token_type": "bearer",
        "role": user.role if user else "student",
    }


@router.post("/logout")
def logout(
    response: Response,
    refresh_token: Optional[str] = Body(None),
    db: Session = Depends(deps.get_db),
):
    if refresh_token:
        db.query(UserSession).filter(
            UserSession.refresh_token == refresh_token
        ).delete()
        db.commit()

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}


# --- Password Recovery Flow ---

import secrets
import string
from app.models.auth import PasswordResetOTP
from app.schemas.auth import (
    PasswordResetRequest,
    PasswordResetVerify,
    PasswordResetConfirm,
    DuplicateEmailResponse,
    StudentProfile,
)


@router.post("/password-reset/request")
def request_password_reset(
    request: PasswordResetRequest,
    student_id: Optional[str] = None,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Request OTP for password reset
    """
    email = request.email.lower()

    # 1. Check for students
    students = (
        db.query(EnrolledStudent).filter(EnrolledStudent.lms_email == email).all()
    )

    # 2. Check for employees (Teachers)
    employee = (
        db.query(EnrolledEmployee).filter(EnrolledEmployee.lms_email == email).first()
    )

    # Handle Duplicate Students
    if not student_id and len(students) > 1:
        profiles = [
            StudentProfile(
                id=str(s.id),
                name=f"{s.first_name} {s.last_name}",
                class_name=s.class_.name if s.class_ else "Unknown",
                roll_number=s.admission_number,
            )
            for s in students
        ]
        return DuplicateEmailResponse(
            message="Multiple profiles found for this email. Please select one.",
            students=profiles,
        )

    # If no email exists anywhere
    if not students and not employee:
        return {"message": "If the email exists, an OTP has been sent."}

    # Generate OTP
    otp_code = "".join(secrets.choice(string.digits) for _ in range(6))
    expires_at = datetime.utcnow() + timedelta(minutes=10)

    # Save OTP
    otp_entry = PasswordResetOTP(email=email, otp_code=otp_code, expires_at=expires_at)
    db.add(otp_entry)
    db.commit()

    # Send Real Email
    from app.utils.email import send_reset_password_email

    email_sent = send_reset_password_email(email, otp_code)

    if not email_sent:
        print(f"FAILED to send OTP email to {email}")

    print(f"DEBUG: OTP for {email} is {otp_code}")

    return {"message": "If the email exists, an OTP has been sent."}


@router.post("/password-reset/verify")
def verify_otp(data: PasswordResetVerify, db: Session = Depends(deps.get_db)) -> Any:
    """
    Verify OTP code
    """
    otp = (
        db.query(PasswordResetOTP)
        .filter(
            PasswordResetOTP.email == data.email.lower(),
            PasswordResetOTP.otp_code == data.otp_code,
            PasswordResetOTP.expires_at > datetime.utcnow(),
            PasswordResetOTP.is_used == False,
        )
        .first()
    )

    if not otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    return {"message": "OTP verified successfully. You can now reset your password."}


@router.post("/password-reset/reset")
def reset_password(
    data: PasswordResetConfirm, db: Session = Depends(deps.get_db)
) -> Any:
    """
    Reset password after OTP verification
    """
    # Verify OTP again to be sure
    otp = (
        db.query(PasswordResetOTP)
        .filter(
            PasswordResetOTP.email == data.email.lower(),
            PasswordResetOTP.otp_code == data.otp_code,
            PasswordResetOTP.expires_at > datetime.utcnow(),
            PasswordResetOTP.is_used == False,
        )
        .first()
    )

    if not otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    # Hash new password
    hashed_password = security.get_password_hash(data.new_password)

    # Update User(s) associated with this email
    users = db.query(User).filter(User.email == data.email.lower()).all()

    # Also Check Students/Employees for this email and update their lms_password
    students = (
        db.query(EnrolledStudent)
        .filter(EnrolledStudent.lms_email == data.email.lower())
        .all()
    )
    employees = (
        db.query(EnrolledEmployee)
        .filter(EnrolledEmployee.lms_email == data.email.lower())
        .all()
    )

    for user in users:
        user.password_hash = hashed_password
        # Invalidate existing sessions
        db.query(UserSession).filter(UserSession.user_id == user.id).delete()

    # Hash and update lms_password for students
    lms_hashed_password = security.get_password_hash(data.new_password)
    for s in students:
        s.lms_password = lms_hashed_password

    # Hash and update lms_password for employees
    for e in employees:
        e.lms_password = lms_hashed_password

    # Mark OTP as used
    otp.is_used = True
    db.commit()

    return {
        "message": "Password reset successfully. You can now log in with your new password."
    }
