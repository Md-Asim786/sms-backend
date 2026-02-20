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


class SubjectType(str, enum.Enum):
    compulsory = "compulsory"
    elective = "elective"


class StudentSubjectStatus(str, enum.Enum):
    active = "active"
    dropped = "dropped"


class SubjectSourceType(str, enum.Enum):
    group = "group"
    manual = "manual"


class ProgramLevel(str, enum.Enum):
    matric = "matric"
    intermediate = "intermediate"


class AcademicYear(Base):
    __tablename__ = "academic_years"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)  # e.g., "2025-2026"
    start_year = Column(Integer, nullable=False)
    end_year = Column(Integer, nullable=False)
    is_current = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    classes = relationship("Class", back_populates="academic_year")


class AcademicGroup(Base):
    __tablename__ = "academic_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(
        String, nullable=False
    )  # Science, Arts, Commerce, Computer Science, Biology
    code = Column(String, unique=True, nullable=False)  # SCI, ART, COM, CS, BIO
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    group_subjects = relationship("GroupSubject", back_populates="group")
    student_enrollments = relationship("StudentGroupEnrollment", back_populates="group")
    classes = relationship(
        "Class",
        secondary="class_groups",
        back_populates="academic_groups",
        overlaps="academic_groups,classes",
    )


class Class(Base):
    __tablename__ = "classes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=True)  # e.g. CLS-9-SCI
    grade_level = Column(Integer, nullable=True)  # e.g., 1, 2, 3... for Class 1, 2, 3
    academic_year_id = Column(
        UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=True
    )

    sections = relationship(
        "Section", back_populates="class_", cascade="all, delete-orphan"
    )
    academic_year = relationship("AcademicYear", back_populates="classes")
    class_subjects = relationship(
        "ClassSubject", back_populates="class_", cascade="all, delete-orphan"
    )
    student_subjects = relationship(
        "StudentSubject", back_populates="class_", cascade="all, delete-orphan"
    )
    teacher_subjects = relationship(
        "TeacherSubject", back_populates="class_", cascade="all, delete-orphan"
    )
    academic_groups = relationship(
        "AcademicGroup",
        secondary="class_groups",
        back_populates="classes",
        overlaps="academic_groups,classes",
    )


class ClassGroup(Base):
    __tablename__ = "class_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    group_id = Column(
        UUID(as_uuid=True), ForeignKey("academic_groups.id"), nullable=False
    )

    class_ = relationship("Class", overlaps="academic_groups,classes")
    group = relationship("AcademicGroup", overlaps="academic_groups,classes")


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
    type = Column(Enum(SubjectType), default=SubjectType.compulsory)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ClassSubject(Base):
    __tablename__ = "class_subjects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    academic_year_id = Column(
        UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=True
    )
    periods_per_week = Column(Integer, default=1)

    class_ = relationship("Class", back_populates="class_subjects")
    subject = relationship("Subject")
    teacher_subjects = relationship("TeacherSubject", back_populates="class_subject")
    student_subjects = relationship("StudentSubject", back_populates="class_subject")


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


class StudentSubject(Base):
    __tablename__ = "student_subjects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(
        UUID(as_uuid=True), ForeignKey("enrolled_students.id"), nullable=False
    )
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    class_subject_id = Column(
        UUID(as_uuid=True), ForeignKey("class_subjects.id"), nullable=False
    )
    academic_year_id = Column(
        UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=True
    )
    source_type = Column(Enum(SubjectSourceType), default=SubjectSourceType.manual)
    status = Column(Enum(StudentSubjectStatus), default=StudentSubjectStatus.active)
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())

    student = relationship("app.models.users.EnrolledStudent")
    class_ = relationship("Class", back_populates="student_subjects")
    subject = relationship("Subject")
    class_subject = relationship("ClassSubject", back_populates="student_subjects")


class GroupSubject(Base):
    __tablename__ = "group_subjects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(
        UUID(as_uuid=True), ForeignKey("academic_groups.id"), nullable=False
    )
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    group = relationship("AcademicGroup", back_populates="group_subjects")
    subject = relationship("Subject")


class StudentGroupEnrollment(Base):
    __tablename__ = "student_group_enrollments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(
        UUID(as_uuid=True), ForeignKey("enrolled_students.id"), nullable=False
    )
    group_id = Column(
        UUID(as_uuid=True), ForeignKey("academic_groups.id"), nullable=False
    )
    academic_year_id = Column(
        UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=True
    )
    is_locked = Column(Boolean, default=False)
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())

    student = relationship("app.models.users.EnrolledStudent")
    group = relationship("AcademicGroup", back_populates="student_enrollments")


class TeacherSubject(Base):
    __tablename__ = "teacher_subjects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    teacher_id = Column(
        UUID(as_uuid=True), ForeignKey("enrolled_employees.id"), nullable=False
    )
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    section_id = Column(UUID(as_uuid=True), ForeignKey("sections.id"), nullable=True)
    group_id = Column(
        UUID(as_uuid=True), ForeignKey("academic_groups.id"), nullable=True
    )
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    class_subject_id = Column(
        UUID(as_uuid=True), ForeignKey("class_subjects.id"), nullable=False
    )
    academic_year_id = Column(
        UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=True
    )
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())

    teacher = relationship("app.models.users.EnrolledEmployee")
    class_ = relationship("Class", back_populates="teacher_subjects")
    section = relationship("Section")
    group = relationship("AcademicGroup")
    subject = relationship("Subject")
    class_subject = relationship("ClassSubject", back_populates="teacher_subjects")


class PromotionHistory(Base):
    __tablename__ = "promotion_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(
        UUID(as_uuid=True), ForeignKey("enrolled_students.id"), nullable=False
    )
    from_class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    to_class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    from_section_id = Column(
        UUID(as_uuid=True), ForeignKey("sections.id"), nullable=True
    )
    to_section_id = Column(UUID(as_uuid=True), ForeignKey("sections.id"), nullable=True)
    from_group_id = Column(
        UUID(as_uuid=True), ForeignKey("academic_groups.id"), nullable=True
    )
    to_group_id = Column(
        UUID(as_uuid=True), ForeignKey("academic_groups.id"), nullable=True
    )
    from_academic_year_id = Column(
        UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=True
    )
    to_academic_year_id = Column(
        UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=True
    )
    exam_result = Column(String, nullable=False)  # PASS or FAIL
    promoted = Column(Boolean, default=True)
    promoted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    promoted_at = Column(DateTime(timezone=True), server_default=func.now())
    is_undone = Column(Boolean, default=False)
    undone_at = Column(DateTime(timezone=True), nullable=True)
    undone_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    student = relationship("app.models.users.EnrolledStudent")
    from_class = relationship("Class", foreign_keys=[from_class_id])
    to_class = relationship("Class", foreign_keys=[to_class_id])
    from_section = relationship("Section", foreign_keys=[from_section_id])
    to_section = relationship("Section", foreign_keys=[to_section_id])
    from_group = relationship("AcademicGroup", foreign_keys=[from_group_id])
    to_group = relationship("AcademicGroup", foreign_keys=[to_group_id])
