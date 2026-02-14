from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID


class DashboardStatsResponse(BaseModel):
    student_applications: int
    total_students_enrolled: int
    employee_applications: int
    total_employees: int

    # Trends (can be hardcoded for now or calculated)
    student_app_trend: str
    student_enrolled_trend: str
    employee_app_trend: str
    employee_trend: str


class ActivityItem(BaseModel):
    id: str
    type: str  # 'application', 'enrollment', 'payment', etc.
    title: str
    description: str
    timestamp: datetime


class DashboardOverviewResponse(BaseModel):
    stats: DashboardStatsResponse
    recent_activity: List[ActivityItem]
    enrollment_chart: List[dict]  # {month: string, count: int}
