from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import List, Optional, Dict
from datetime import time, datetime

from app.schemas.lms import SubjectResponse
from app.schemas.users import EnrolledEmployeeResponse


class RoomBase(BaseModel):
    name: str
    capacity: Optional[int] = None
    room_type: Optional[str] = None
    is_lab: Optional[bool] = False
    description: Optional[str] = None
    is_active: Optional[bool] = True

class RoomCreate(RoomBase):
    pass

class Room(RoomBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


class TimetableConfigBase(BaseModel):
    model_config = ConfigDict(extra="ignore")
    academic_year_id: UUID
    working_days: List[str]
    start_time: time
    end_time: time
    slot_duration: int
    periods_per_day: int = 6
    break_details: Optional[List[Dict]] = None
    max_periods_per_teacher_day: Optional[int] = None
    max_periods_per_teacher_week: Optional[int] = None

class TimetableConfigCreate(TimetableConfigBase):
    pass

class TimetableConfig(TimetableConfigBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True, extra="ignore")


class TimetableConfigUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    working_days: Optional[List[str]] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    slot_duration: Optional[int] = None
    periods_per_day: Optional[int] = None
    break_details: Optional[List[Dict]] = None
    max_periods_per_teacher_day: Optional[int] = None
    max_periods_per_teacher_week: Optional[int] = None


class TimetableSlotBase(BaseModel):
    day: str
    period_index: int
    start_time: time
    end_time: time
    subject_id: UUID
    teacher_id: UUID
    room_id: Optional[UUID] = None
    class_id: UUID
    section_id: Optional[UUID] = None
    is_manual: bool = False
    is_locked: bool = False
    is_double_period: bool = False

class TimetableSlotCreate(TimetableSlotBase):
    version_id: UUID

class TimetableSlot(TimetableSlotBase):
    id: UUID
    subject: Optional[SubjectResponse] = None
    teacher: Optional[EnrolledEmployeeResponse] = None
    room: Optional[Room] = None
    model_config = ConfigDict(from_attributes=True)


class TimetableVersionBase(BaseModel):
    name: str
    academic_year_id: UUID
    is_active: bool = False
    is_locked: bool = False

class TimetableVersionCreate(TimetableVersionBase):
    pass

class TimetableVersion(TimetableVersionBase):
    id: UUID
    slots: List[TimetableSlot] = []
    model_config = ConfigDict(from_attributes=True)


class TeacherConstraintBase(BaseModel):
    teacher_id: UUID
    academic_year_id: UUID
    max_periods_per_day: Optional[int] = None
    max_periods_per_week: Optional[int] = None
    unavailable_slots: Optional[List[Dict]] = None

class TeacherConstraintCreate(TeacherConstraintBase):
    pass

class TeacherConstraint(TeacherConstraintBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


class SubjectConstraintBase(BaseModel):
    class_subject_id: UUID
    is_lab: bool = False
    requires_double_period: bool = False
    is_core: bool = False
    difficulty_level: int = 1

class SubjectConstraintCreate(SubjectConstraintBase):
    pass

class SubjectConstraint(SubjectConstraintBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


# Generation Request
class TimetableGenerationRequest(BaseModel):
    academic_year_id: UUID
    version_name: str
    class_ids: Optional[List[UUID]] = None  # If None, generate for all
    preserve_locked: bool = True


TimetableSlot.model_rebuild()
TimetableVersion.model_rebuild()
