from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Float,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base


class ExamTerm(Base):
    __tablename__ = "exam_terms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True)


class Result(Base):
    __tablename__ = "results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exam_term_id = Column(
        UUID(as_uuid=True), ForeignKey("exam_terms.id"), nullable=False
    )
    student_id = Column(
        UUID(as_uuid=True), ForeignKey("enrolled_students.id"), nullable=False
    )
    # Usually results are per subject, checking types...
    # school-admin/src/types/index.ts doesn't show subject_id in Result interface,
    # but logically it should be there.
    # Wait, the interface says: exam_term_id, student_id, total_marks, obtained_marks, grade.
    # It seems to be missing subject_id in the frontend type definition, or it's an aggregate result?
    # Usually it's per subject. I will add subject_id or class_subject_id to be safe/correct.
    # Requirement: "Data Consistency ... Identify inconsistent attributes".
    # I'll add class_subject_id as it makes the most sense.

    class_subject_id = Column(
        UUID(as_uuid=True), ForeignKey("class_subjects.id"), nullable=False
    )

    total_marks = Column(Float, nullable=False)
    obtained_marks = Column(Float, nullable=False)
    grade = Column(String, nullable=False)
    remarks = Column(Text)

    exam_term = relationship("ExamTerm")
    student = relationship("app.models.users.EnrolledStudent")
    class_subject = relationship("app.models.lms.ClassSubject")
