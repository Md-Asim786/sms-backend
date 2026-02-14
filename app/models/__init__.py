from app.core.database import Base
from app.models.auth import User
from app.models.applications import StudentApplication, EmployeeApplication
from app.models.users import EnrolledStudent, EnrolledEmployee
from app.models.lms import (
    Class,
    Section,
    Subject,
    ClassSubject,
    Assignment,
    Lecture,
    AttendanceRecord,
)
from app.models.exams import ExamTerm, Result
from app.models.finance import SalaryRecord, FeePayment
from app.models.communication import Message, ContactMessage
from app.models.website import (
    SchoolConfig,
    JobCategory,
    JobPosition,
    News,
    LeadershipMember,
)
