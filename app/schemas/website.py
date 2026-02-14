from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class SchoolConfigBase(BaseModel):
    is_admission_open: bool = False
    admission_deadline: Optional[str] = None
    application_deadlines: List[Dict[str, str]] = []
    required_documents: List[str] = []
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    interview_location: Optional[str] = None
    interview_time_range: Optional[str] = None
    challan_due_days: int = 7
    admission_fee: int = 0
    tuition_fee_base: int = 0
    google_form_link: Optional[str] = None


class SchoolConfigResponse(SchoolConfigBase):
    id: UUID
    updated_at: datetime

    class Config:
        from_attributes = True


class FeePaymentBase(BaseModel):
    challan_number: str
    amount: int
    status: str = "pending"
    payment_date: Optional[datetime] = None
    receipt_url: Optional[str] = None


class FeePaymentResponse(FeePaymentBase):
    id: UUID
    student_id: Optional[UUID] = None
    application_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


class JobPositionBase(BaseModel):
    category_id: UUID
    title: str


class JobPositionResponse(JobPositionBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class JobCategoryBase(BaseModel):
    title: str
    description: Optional[str] = None
    requirements: Optional[List[str]] = None
    apply_link: Optional[str] = None


class JobCategoryResponse(JobCategoryBase):
    id: UUID
    created_at: datetime
    positions: List[JobPositionResponse] = []

    class Config:
        from_attributes = True


class NewsBase(BaseModel):
    title: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    published_date: Optional[datetime] = None


class NewsResponse(NewsBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class LeadershipMemberBase(BaseModel):
    name: str
    position: str
    image_url: Optional[str] = None
    bio: Optional[str] = None
    quote: Optional[str] = None
    display_order: int = 0


class LeadershipMemberResponse(LeadershipMemberBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
