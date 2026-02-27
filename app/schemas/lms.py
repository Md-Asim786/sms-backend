from __future__ import annotations
from typing import List, Optional, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from app.models.lms import (
    AttendanceStatus,
    SubjectType,
    StudentSubjectStatus,
    SubjectSourceType,
    ProgramLevel,
    LectureType,
)
from app.schemas.users import EnrolledStudentResponse, EnrolledEmployeeResponse


class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None


class AcademicYearBase(BaseModel):
    name: str
    start_year: int
    end_year: int
    is_current: bool = False


class AcademicYearCreate(AcademicYearBase):
    pass


class AcademicYearResponse(AcademicYearBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class ClassBase(BaseModel):
    name: str
    code: Optional[str] = None
    grade_level: Optional[int] = None
    academic_year_id: Optional[UUID] = None
    group_ids: Optional[List[UUID]] = None


class ClassResponseWithGroups(ClassBase):
    id: UUID
    academic_groups: Optional[List["AcademicGroupResponse"]] = []

    class Config:
        from_attributes = True


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
    type: SubjectType = SubjectType.compulsory


class SubjectCreate(SubjectBase):
    pass


class SubjectResponse(SubjectBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class ClassSubjectBase(BaseModel):
    class_id: UUID
    subject_id: UUID
    academic_year_id: Optional[UUID] = None
    periods_per_week: int = 1
    attachments: Optional[List[str]] = None


class ClassSubjectCreate(ClassSubjectBase):
    pass


class AssignmentBase(BaseModel):
    class_subject_id: UUID
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    attachments: Optional[List[str]] = None
    allow_reupload: bool = True
    max_file_size_mb: int = 10
    allowed_file_types: Optional[List[str]] = None


class AssignmentCreate(AssignmentBase):
    pass


class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    attachments: Optional[List[str]] = None
    allow_reupload: Optional[bool] = None
    max_file_size_mb: Optional[int] = None
    allowed_file_types: Optional[List[str]] = None


class AssignmentResponse(AssignmentBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class AssignmentWithSubmissions(AssignmentResponse):
    submission_count: Optional[int] = 0
    graded_count: Optional[int] = 0


class ClassSubjectResponse(ClassSubjectBase):
    id: UUID
    subject: SubjectResponse

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


class AttendanceUpdate(BaseModel):
    status: Optional[AttendanceStatus] = None
    reason: Optional[str] = None


class AttendanceResponse(AttendanceBase):
    id: UUID
    marked_by_id: Optional[UUID] = None
    reason: Optional[str] = None
    audit_logs: Optional[List[dict]] = None

    class Config:
        from_attributes = True


class BulkAttendanceRequest(BaseModel):
    class_subject_id: UUID
    date: datetime
    records: List[AttendanceBase]


class AttendanceStats(BaseModel):
    total_classes: int
    present: int
    absent: int
    late: int
    excused: int
    percentage: float


class AssignmentSubmissionBase(BaseModel):
    assignment_id: UUID
    student_id: UUID
    file_url: str
    grade: Optional[str] = None
    feedback: Optional[str] = None


class AssignmentSubmissionCreate(AssignmentSubmissionBase):
    pass


class AssignmentSubmissionUpdate(BaseModel):
    file_url: Optional[str] = None
    grade: Optional[str] = None
    feedback: Optional[str] = None


class AssignmentSubmissionResponse(AssignmentSubmissionBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GradeSubmissionRequest(BaseModel):
    grade: str
    feedback: Optional[str] = None


class LectureBase(BaseModel):
    class_subject_id: UUID
    title: str
    description: Optional[str] = None
    content_url: Optional[str] = None
    type: LectureType = LectureType.other
    is_published: bool = False
    author_id: Optional[UUID] = None
    attachments: Optional[List[str]] = None
    scheduled_at: Optional[datetime] = None


class LectureCreate(LectureBase):
    pass


class LectureUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content_url: Optional[str] = None
    type: Optional[LectureType] = None
    is_published: Optional[bool] = None
    attachments: Optional[List[str]] = None
    scheduled_at: Optional[datetime] = None


class LectureResponse(LectureBase):
    id: UUID
    view_count: int = 0
    download_count: int = 0

    class Config:
        from_attributes = True


class StudentSubjectBase(BaseModel):
    student_id: UUID
    class_id: UUID
    subject_id: UUID
    class_subject_id: UUID
    academic_year_id: Optional[UUID] = None
    status: StudentSubjectStatus = StudentSubjectStatus.active


class StudentSubjectCreate(StudentSubjectBase):
    pass


class StudentSubjectResponse(StudentSubjectBase):
    id: UUID
    enrolled_at: datetime

    class Config:
        from_attributes = True


class TeacherSubjectBase(BaseModel):
    teacher_id: UUID
    class_id: UUID
    section_id: Optional[UUID] = None
    group_id: Optional[UUID] = None
    subject_id: UUID
    class_subject_id: UUID
    academic_year_id: Optional[UUID] = None


class TeacherSubjectCreate(TeacherSubjectBase):
    pass


class TeacherSubjectResponse(TeacherSubjectBase):
    id: UUID
    assigned_at: datetime
    teacher: Optional[EnrolledEmployeeResponse] = None
    subject: Optional[SubjectResponse] = None
    class_: Optional[ClassResponse] = None
    section: Optional[SectionResponse] = None
    group: Optional[AcademicGroupResponse] = None

    class Config:
        from_attributes = True


# Academic Group Schemas
class AcademicGroupBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    is_active: bool = True


class AcademicGroupCreate(AcademicGroupBase):
    class_ids: Optional[List[UUID]] = None


class AcademicGroupResponse(AcademicGroupBase):
    id: UUID
    created_at: datetime
    classes: Optional[List["ClassResponse"]] = []

    class Config:
        from_attributes = True


class GroupSubjectBase(BaseModel):
    group_id: UUID
    subject_id: UUID


class GroupSubjectCreate(GroupSubjectBase):
    pass


class GroupSubjectResponse(GroupSubjectBase):
    id: UUID
    subject: SubjectResponse

    class Config:
        from_attributes = True


class GroupSubjectMapping(BaseModel):
    subject_id: UUID


class BulkGroupSubjectCreate(BaseModel):
    group_id: UUID
    subjects: List[GroupSubjectMapping]


# Student Group Enrollment Schemas
class StudentGroupEnrollmentBase(BaseModel):
    student_id: UUID
    group_id: UUID
    academic_year_id: Optional[UUID] = None
    is_locked: bool = False


class StudentGroupEnrollmentCreate(StudentGroupEnrollmentBase):
    pass


class StudentGroupEnrollmentResponse(StudentGroupEnrollmentBase):
    id: UUID
    enrolled_at: datetime
    group: AcademicGroupResponse

    class Config:
        from_attributes = True


# Updated StudentSubject with source_type
class StudentSubjectResponseExtended(StudentSubjectBase):
    id: UUID
    enrolled_at: datetime
    source_type: SubjectSourceType

    class Config:
        from_attributes = True


# Promotion History Schemas
class PromotionHistoryBase(BaseModel):
    student_id: UUID
    from_class_id: UUID
    to_class_id: UUID
    from_section_id: Optional[UUID] = None
    to_section_id: Optional[UUID] = None
    from_group_id: Optional[UUID] = None
    to_group_id: Optional[UUID] = None
    from_academic_year_id: Optional[UUID] = None
    to_academic_year_id: Optional[UUID] = None
    exam_result: str
    promoted: bool = True


class PromotionHistoryCreate(PromotionHistoryBase):
    pass


class PromotionHistoryResponse(PromotionHistoryBase):
    id: UUID
    promoted_at: datetime
    is_undone: bool = False
    undone_at: Optional[datetime] = None
    student: Optional[EnrolledStudentResponse] = None
    from_class: Optional[ClassResponse] = None
    to_class: Optional[ClassResponse] = None

    class Config:
        from_attributes = True


class StudentExamStatus(BaseModel):
    student_id: UUID
    student_name: str
    student_roll_number: Optional[str] = None
    exam_result: str
    total_marks: float
    obtained_marks: float
    percentage: float
    grade: str


class PromoteStudentsRequest(BaseModel):
    student_ids: List[UUID]
    to_class_id: UUID
    to_section_id: Optional[UUID] = None
    to_group_id: Optional[UUID] = None
    to_academic_year_id: Optional[UUID] = None
    promote_all_eligible: bool = False
    promote_all_except: bool = False
    allow_failed: bool = False
