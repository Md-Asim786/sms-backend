from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum
from app.core.database import Base


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    verified = "verified"
    rejected = "rejected"


class SalaryRecord(Base):
    __tablename__ = "salary_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(
        UUID(as_uuid=True), ForeignKey("enrolled_employees.id"), nullable=False
    )
    amount = Column(Integer, nullable=False)
    payment_date = Column(DateTime(timezone=True))
    status = Column(Enum(PaymentStatus), default=PaymentStatus.pending)
    month_year = Column(String, nullable=False)  # e.g. "05-2026"

    employee = relationship("app.models.users.EnrolledEmployee")


class FeePayment(Base):
    __tablename__ = "fee_payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(
        UUID(as_uuid=True), ForeignKey("enrolled_students.id"), nullable=True
    )
    application_id = Column(
        UUID(as_uuid=True), ForeignKey("student_applications.id"), nullable=True
    )
    challan_number = Column(String, unique=True, nullable=False)
    amount = Column(Integer, nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.pending)
    payment_date = Column(DateTime(timezone=True))
    receipt_url = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    student = relationship("app.models.users.EnrolledStudent")
    application = relationship("app.models.applications.StudentApplication")
