from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Integer,
    JSON,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class SchoolConfig(Base):
    __tablename__ = "school_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    is_admission_open = Column(Boolean, default=False)
    admission_deadline = Column(String, nullable=True)
    application_deadlines = Column(JSON)  # Array of {label, date}
    required_documents = Column(JSON)  # Array of strings
    contact_email = Column(String)
    contact_phone = Column(String)
    interview_location = Column(String)
    interview_time_range = Column(String)
    challan_due_days = Column(Integer, default=7)
    admission_fee = Column(Integer, default=0)
    tuition_fee_base = Column(Integer, default=0)
    google_form_link = Column(String)

    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class JobCategory(Base):
    __tablename__ = "job_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(Text)
    requirements = Column(JSON)
    apply_link = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    positions = relationship(
        "JobPosition", back_populates="category", cascade="all, delete-orphan"
    )


class JobPosition(Base):
    __tablename__ = "job_positions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id = Column(
        UUID(as_uuid=True), ForeignKey("job_categories.id", ondelete="CASCADE")
    )
    title = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    category = relationship("JobCategory", back_populates="positions")


class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    image_url = Column(String)
    published_date = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class LeadershipMember(Base):
    __tablename__ = "leadership_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    position = Column(String, nullable=False)
    image_url = Column(String)
    bio = Column(Text)
    quote = Column(Text)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
