from pydantic import BaseModel, Field
from typing import Optional, List, Union
from datetime import datetime
from uuid import UUID


class StudentApplicationBase(BaseModel):
    first_name: str
    last_name: str
    gender: str
    date_of_birth: str
    b_form_number: Optional[str] = None  # Added
    guardian_name: str
    guardian_cnic: str
    guardian_phone: str
    guardian_email: str
    city: str
    address: str
    applying_for_class: str
    previous_school: Optional[str] = None


class StudentApplicationCreate(StudentApplicationBase):
    pass


class StudentApplicationUpdate(BaseModel):
    status: Optional[str] = None


class StudentApplicationResponse(StudentApplicationBase):
    id: UUID
    regId: str
    status: str
    student_photo_url: Optional[str] = None
    applied_at: datetime
    reviewed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EmployeeApplicationBase(BaseModel):
    first_name: str
    last_name: str
    gender: str
    date_of_birth: str
    phone: str
    email: str
    cnic: str
    position_applied_for: str
    subject: Optional[str] = None
    highest_qualification: str
    experience_years: str
    current_organization: Optional[str] = None


class EmployeeApplicationCreate(EmployeeApplicationBase):
    pass


class EmployeeApplicationResponse(EmployeeApplicationBase):
    id: UUID
    status: str
    cv_url: Optional[str] = None
    photo_url: Optional[str] = None
    applied_at: datetime
    reviewed_at: Optional[datetime] = None
    interview_date: Optional[str] = None
    interview_time: Optional[str] = None
    interview_location: Optional[str] = None
    interview_notes: Optional[str] = None

    class Config:
        from_attributes = True
