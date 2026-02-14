from typing import List, Optional, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from app.models.lms import AttendanceStatus


class ClassBase(BaseModel):
    name: str
    code: Optional[str] = None
    group: Optional[str] = None


class ClassCreate(ClassBase):
    pass


class ClassResponse(ClassBase):
    id: UUID

    class Config:
        from_attributes = True


class SectionBase(BaseModel):
    name: str
    capacity: Optional[int] = 30  # Allow None and default to 30
    class_id: UUID


class SectionCreate(SectionBase):
    pass


class SectionResponse(SectionBase):
    id: UUID
    student_count: Optional[int] = 0  # To show current enrollment

    class Config:
        from_attributes = True


class SubjectBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None


class SubjectCreate(SubjectBase):
    pass


class SubjectResponse(SubjectBase):
    id: UUID

    class Config:
        from_attributes = True


class ClassSubjectBase(BaseModel):
    class_id: UUID
    subject_id: UUID
    teacher_id: Optional[UUID] = None


class ClassSubjectCreate(ClassSubjectBase):
    pass


class ClassSubjectResponse(ClassSubjectBase):
    id: UUID
    subject: SubjectResponse
    teacher: Optional[Any] = (
        None  # Using Any to avoid circular dependency with EnrolledEmployee
    )

    class Config:
        from_attributes = True


class BulkSectionItem(BaseModel):
    name: str
    capacity: int = 30


class BulkSectionCreate(BaseModel):
    class_id: UUID
    sections: List[BulkSectionItem]


class SubjectMapping(BaseModel):
    subject_id: UUID
    teacher_id: Optional[UUID] = None


class BulkMappingCreate(BaseModel):
    class_id: UUID
    mappings: List[SubjectMapping]


class BulkClassCreate(BaseModel):
    classes: List[ClassCreate]


class AttendanceBase(BaseModel):
    student_id: UUID
    class_subject_id: UUID
    date: datetime
    status: AttendanceStatus


class AttendanceCreate(AttendanceBase):
    pass


class AttendanceResponse(AttendanceBase):
    id: UUID

    class Config:
        from_attributes = True
