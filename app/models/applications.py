from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Integer,
    JSON,
    ForeignKey,
    Enum,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.core.database import Base
import enum


class StudentApplicationStatus(str, enum.Enum):
    applied = "applied"
    reviewed = "reviewed"
    pending_verification = "pending_verification"
    accepted = "accepted"
    rejected = "rejected"


class EmployeeApplicationStatus(str, enum.Enum):
    applied = "applied"
    shortlisted = "shortlisted"
    interviewed = "interviewed"
    hired = "hired"
    rejected = "rejected"


class StudentApplication(Base):
    __tablename__ = "student_applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    regId = Column(String, unique=True, index=True, nullable=False)
    status = Column(
        Enum(StudentApplicationStatus), default=StudentApplicationStatus.applied
    )

    # Student Info
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    date_of_birth = Column(String, nullable=False)
    student_photo_url = Column(String)

    # Guardian Info
    guardian_name = Column(String, nullable=False)
    guardian_cnic = Column(String, nullable=False)
    guardian_phone = Column(String, nullable=False)
    guardian_email = Column(String, nullable=False)

    # Contact & Academic
    city = Column(String, nullable=False)
    address = Column(Text, nullable=False)
    b_form_number = Column(String, nullable=True)  # Added for enrollment
    applying_for_class = Column(String, nullable=False)
    group_id = Column(
        UUID(as_uuid=True), ForeignKey("academic_groups.id"), nullable=True
    )
    previous_school = Column(String)

    applied_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True))


class EmployeeApplication(Base):
    __tablename__ = "employee_applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(
        Enum(EmployeeApplicationStatus), default=EmployeeApplicationStatus.applied
    )

    # Personal Info
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    date_of_birth = Column(String, nullable=False)
    photo_url = Column(String)

    # Contact
    phone = Column(String, nullable=False)
    email = Column(String, nullable=False)
    cnic = Column(String, nullable=False)

    # Professional
    position_applied_for = Column(String, nullable=False)
    subject = Column(String)  # Legacy field - stores comma-separated subject names
    subjects = Column(String)  # New field - stores comma-separated subject IDs
    highest_qualification = Column(Text, nullable=False)
    experience_years = Column(String, nullable=False)
    cv_url = Column(String, nullable=False)
    current_organization = Column(Text)

    applied_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True))
    reviewed_by_admin_id = Column(UUID(as_uuid=True), nullable=True)

    # Interview Details
    interview_date = Column(String, nullable=True)
    interview_time = Column(String, nullable=True)
    interview_location = Column(String, nullable=True)
    interview_notes = Column(Text, nullable=True)
