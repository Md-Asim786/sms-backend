from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Enum as SQLAEnum,
    Text,
    Integer,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.core.database import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    teacher = "teacher"
    staff = "staff"
    student = "student"


class EnrolledStudent(Base):
    __tablename__ = "enrolled_students"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reg_id = Column(String, unique=True)
    system_student_id = Column(String, unique=True, nullable=False)  # STU-2026-001
    admission_number = Column(String, unique=True, nullable=False)  # SCH-2026123

    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    date_of_birth = Column(String, nullable=False)
    student_photo_url = Column(String)

    b_form_number = Column(String, nullable=False)
    student_cnic = Column(String)

    guardian_name = Column(String, nullable=False)
    guardian_cnic = Column(String, nullable=False)
    guardian_phone = Column(String, nullable=False)
    guardian_email = Column(String, nullable=False)

    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    section_id = Column(UUID(as_uuid=True), ForeignKey("sections.id"), nullable=False)
    group_id = Column(
        UUID(as_uuid=True), ForeignKey("academic_groups.id"), nullable=True
    )  # For classes 9-12
    applying_for_class = Column(String)
    city = Column(String)
    address = Column(Text)

    # Linked User Account
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    lms_email = Column(String, unique=True, nullable=False)
    lms_login = Column(String, unique=True, nullable=False)
    lms_password = Column(String)

    class_ = relationship("app.models.lms.Class")
    section = relationship("app.models.lms.Section")
    group = relationship("app.models.lms.AcademicGroup")
    user = relationship("app.models.auth.User")

    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)


class EnrolledEmployee(Base):
    __tablename__ = "enrolled_employees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(String, unique=True, nullable=False)  # EMP-2026-001

    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    date_of_birth = Column(String, nullable=False)
    photo_url = Column(String)

    phone = Column(String, nullable=False)
    email = Column(String, nullable=False)
    cnic = Column(String, nullable=False)

    employee_type = Column(
        String, nullable=False
    )  # teaching, academic_support, non_academic
    functional_role = Column(String, nullable=False)
    system_role = Column(
        String, nullable=False
    )  # teacher, staff, admin, no_system_access
    subject = Column(String)

    highest_qualification = Column(Text, nullable=False)
    experience_years = Column(String, nullable=False)
    current_organization = Column(Text)
    cv_url = Column(String)

    # Linked User Account
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    lms_email = Column(String, unique=True, nullable=True)
    lms_login = Column(String, unique=True, nullable=True)
    lms_password = Column(String)

    user = relationship("app.models.auth.User")

    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
