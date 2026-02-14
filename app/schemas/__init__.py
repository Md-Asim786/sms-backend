from app.schemas.applications import (
    StudentApplicationCreate,
    StudentApplicationUpdate,
    StudentApplicationResponse,
    EmployeeApplicationCreate,
    EmployeeApplicationResponse,
)
from app.schemas.users import (
    EnrolledStudentBase,
    EnrolledStudentUpdate,
    EnrolledStudentResponse,
    EnrolledEmployeeBase,
    EnrolledEmployeeUpdate,
    EnrolledEmployeeResponse,
)
from app.schemas.website import (
    SchoolConfigBase,
    SchoolConfigResponse,
    JobCategoryBase,
    JobCategoryResponse,
    JobPositionBase,
    JobPositionResponse,
    NewsBase,
    NewsResponse,
    LeadershipMemberBase,
    LeadershipMemberResponse,
    FeePaymentBase,
    FeePaymentResponse,
)
from app.schemas.dashboard import (
    DashboardOverviewResponse,
    DashboardStatsResponse,
    ActivityItem,
)
