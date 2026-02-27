from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Integer,
    Time,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base


class Room(Base):
    __tablename__ = "rooms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    capacity = Column(Integer, nullable=True)
    room_type = Column(String, nullable=True)  # Classroom, Lab
    is_lab = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    slots = relationship("TimetableSlot", back_populates="room")


class TimetableConfig(Base):
    __tablename__ = "timetable_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    academic_year_id = Column(
        UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False
    )
    working_days = Column(JSON, nullable=False)  # List of days e.g. ["Monday", "Tuesday", ...]
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    slot_duration = Column(Integer, nullable=False)  # in minutes
    periods_per_day = Column(Integer, nullable=False, default=6)
    break_details = Column(JSON, nullable=True)  # List of dicts: {"after_period": 2, "duration": 30}
    max_periods_per_teacher_day = Column(Integer, nullable=True)
    max_periods_per_teacher_week = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    academic_year = relationship("AcademicYear")


class TimetableVersion(Base):
    __tablename__ = "timetable_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    academic_year_id = Column(
        UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False
    )
    name = Column(String, nullable=False)  # e.g., "Main Schedule 2026", "Draft 1"
    is_active = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    academic_year = relationship("AcademicYear")
    slots = relationship("TimetableSlot", back_populates="version", cascade="all, delete-orphan")


class TimetableSlot(Base):
    __tablename__ = "timetable_slots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version_id = Column(UUID(as_uuid=True), ForeignKey("timetable_versions.id"), nullable=False)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    section_id = Column(UUID(as_uuid=True), ForeignKey("sections.id"), nullable=True)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("enrolled_employees.id"), nullable=False)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=True)
    day = Column(String, nullable=False)
    period_index = Column(Integer, nullable=False)  # 0-indexed position in the day
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_manual = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    is_double_period = Column(Boolean, default=False)

    version = relationship("TimetableVersion", back_populates="slots")
    class_ = relationship("Class")
    section = relationship("Section")
    subject = relationship("Subject")
    teacher = relationship("EnrolledEmployee")
    room = relationship("Room", back_populates="slots")


class TeacherConstraint(Base):
    __tablename__ = "teacher_constraints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("enrolled_employees.id"), nullable=False)
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False)
    max_periods_per_day = Column(Integer, nullable=True)
    max_periods_per_week = Column(Integer, nullable=True)
    unavailable_slots = Column(JSON, nullable=True)  # List of {"day": "Monday", "period_index": 1}
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    teacher = relationship("EnrolledEmployee")
    academic_year = relationship("AcademicYear")


class SubjectConstraint(Base):
    __tablename__ = "subject_constraints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_subject_id = Column(UUID(as_uuid=True), ForeignKey("class_subjects.id"), nullable=False, unique=True)
    is_lab = Column(Boolean, default=False)
    requires_double_period = Column(Boolean, default=False)
    is_core = Column(Boolean, default=False)
    difficulty_level = Column(Integer, default=1)  # 1: Light, 2: Medium, 3: Heavy
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    class_subject = relationship("ClassSubject")
