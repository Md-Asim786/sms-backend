from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.api.v1 import (
    admin_router,
    website_router,
    auth_router,
    students_router,
    lms_router,
)

app = FastAPI(
    title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS
origins = [
    "http://localhost:3000",  # school-admin
    "http://localhost:3001",  # school-website
    "http://localhost:3002",  # school-student-portal
    "http://localhost:3003",  # school-lms
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Mount static files for uploads
if not os.path.exists(settings.UPLOAD_DIR):
    os.makedirs(settings.UPLOAD_DIR)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "photos"))
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "cvs"))

app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include Routers
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["Auth"])
app.include_router(admin_router, prefix=f"{settings.API_V1_STR}/admin", tags=["Admin"])
app.include_router(
    website_router, prefix=f"{settings.API_V1_STR}/website", tags=["Website"]
)
app.include_router(
    students_router, prefix=f"{settings.API_V1_STR}/students", tags=["Students"]
)
app.include_router(lms_router, prefix=f"{settings.API_V1_STR}/lms", tags=["LMS"])


@app.get("/")
async def root():
    return {"message": "Welcome to School Admin Portal API"}
