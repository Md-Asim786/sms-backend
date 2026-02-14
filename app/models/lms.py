from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Enum,
    Integer,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum
from app.core.database import Base


class AttendanceStatus(str, enum.Enum):
    present = "present"
    absent = "absent"
    late = "late"
    excused = "excused"


class Class(Base):
    __tablename__ = "classes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=True)  # e.g. CLS-9-SCI
    group = Column(String, nullable=True)  # Science, Arts, etc.

    sections = relationship("Section", back_populates="class_")


class Section(Base):
    __tablename__ = "sections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    capacity = Column(Integer, default=30)  # Default capacity
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)

    class_ = relationship("Class", back_populates="sections")
    students = relationship(
        "app.models.users.EnrolledStudent", back_populates="section"
    )


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)
    description = Column(Text)


class ClassSubject(Base):
    __tablename__ = "class_subjects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    teacher_id = Column(
        UUID(as_uuid=True), ForeignKey("enrolled_employees.id"), nullable=True
    )

    # relationships
    class_ = relationship("Class")
    subject = relationship("Subject")
    teacher = relationship("app.models.users.EnrolledEmployee")


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_subject_id = Column(
        UUID(as_uuid=True), ForeignKey("class_subjects.id"), nullable=False
    )
    title = Column(String, nullable=False)
    description = Column(Text)
    due_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    class_subject = relationship("ClassSubject")


class Lecture(Base):
    __tablename__ = "lectures"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_subject_id = Column(
        UUID(as_uuid=True), ForeignKey("class_subjects.id"), nullable=False
    )
    title = Column(String, nullable=False)
    description = Column(Text)
    content_url = Column(String)
    scheduled_at = Column(DateTime(timezone=True))

    class_subject = relationship("ClassSubject")


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(
        UUID(as_uuid=True), ForeignKey("enrolled_students.id"), nullable=False
    )
    class_subject_id = Column(
        UUID(as_uuid=True), ForeignKey("class_subjects.id"), nullable=False
    )
    date = Column(DateTime(timezone=True), nullable=False)
    status = Column(Enum(AttendanceStatus), nullable=False)

    student = relationship("app.models.users.EnrolledStudent")
    class_subject = relationship("ClassSubject")
