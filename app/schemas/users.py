from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# --- Enrolled Student Schemas ---


class EnrolledStudentBase(BaseModel):
    reg_id: Optional[str] = None
    system_student_id: str
    admission_number: str
    first_name: str
    last_name: str
    gender: str
    date_of_birth: str
    student_photo_url: Optional[str] = None
    b_form_number: str
    student_cnic: Optional[str] = None
    guardian_name: str
    guardian_cnic: str
    guardian_phone: str
    guardian_email: str
    class_id: UUID
    section_id: UUID
    applying_for_class: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    lms_email: str
    lms_login: str
    lms_password: str


class EnrolledStudentResponse(EnrolledStudentBase):
    id: UUID
    enrolled_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class EnrolledStudentUpdate(BaseModel):
    reg_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[str] = None
    student_photo_url: Optional[str] = None
    b_form_number: Optional[str] = None
    student_cnic: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_cnic: Optional[str] = None
    guardian_phone: Optional[str] = None
    guardian_email: Optional[str] = None
    class_id: Optional[UUID] = None
    section_id: Optional[UUID] = None
    group_id: Optional[UUID] = None
    applying_for_class: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    lms_email: Optional[str] = None
    lms_login: Optional[str] = None
    lms_password: Optional[str] = None
    is_active: Optional[bool] = None


# --- Enrolled Employee Schemas ---


class EnrolledEmployeeBase(BaseModel):
    employee_id: str
    first_name: str
    last_name: str
    gender: str
    date_of_birth: str
    photo_url: Optional[str] = None
    phone: str
    email: str
    cnic: str
    employee_type: str
    functional_role: str
    system_role: str
    subject: Optional[str] = None
    highest_qualification: str
    experience_years: str
    current_organization: Optional[str] = None
    cv_url: Optional[str] = None
    lms_email: Optional[str] = None
    lms_login: Optional[str] = None
    lms_password: Optional[str] = None


class EnrolledEmployeeCreate(BaseModel):
    first_name: str
    last_name: str
    gender: str
    date_of_birth: str
    phone: str
    email: str
    cnic: str
    employee_type: str
    functional_role: str
    system_role: str
    subject: Optional[str] = None
    highest_qualification: str
    experience_years: str
    current_organization: Optional[str] = None
    photo_url: Optional[str] = None


class EnrolledEmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[str] = None
    photo_url: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    cnic: Optional[str] = None
    employee_type: Optional[str] = None
    functional_role: Optional[str] = None
    system_role: Optional[str] = None
    subject: Optional[str] = None
    highest_qualification: Optional[str] = None
    experience_years: Optional[str] = None
    current_organization: Optional[str] = None
    cv_url: Optional[str] = None
    lms_email: Optional[str] = None
    lms_login: Optional[str] = None
    lms_password: Optional[str] = None
    is_active: Optional[bool] = None


class EnrolledEmployeeResponse(EnrolledEmployeeBase):
    id: UUID
    joined_at: datetime
    is_active: bool

    class Config:
        from_attributes = True
