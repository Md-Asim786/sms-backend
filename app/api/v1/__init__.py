from fastapi import APIRouter
from app.api.v1.admin import router as admin_router
from app.api.v1.website import router as website_router
from app.api.v1.auth import router as auth_router
from app.api.v1.students import router as students_router
from app.api.v1.lms import router as lms_router
from app.api.v1.timetable import router as timetable_router
from app.api.v1.user_profile import router as user_profile_router

__all__ = [
    "admin_router",
    "website_router",
    "auth_router",
    "students_router",
    "lms_router",
    "timetable_router",
    "user_profile_router",
]
