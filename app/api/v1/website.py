from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime
import os
import shutil

from app.core.database import get_db
from app.models import (
    News,
    JobCategory,
    JobPosition,
    LeadershipMember,
    StudentApplication,
    EmployeeApplication,
    SchoolConfig,
    Subject,
)
from app.models.applications import StudentApplicationStatus, EmployeeApplicationStatus
from app.schemas import (
    NewsResponse,
    JobCategoryResponse,
    LeadershipMemberResponse,
    StudentApplicationCreate,
    StudentApplicationResponse,
    EmployeeApplicationResponse,
    SchoolConfigResponse,
)
from app.schemas.lms import SubjectResponse
from app.core.config import settings

from app.models.lms import Class
from app.schemas.lms import ClassResponse

router = APIRouter()


# Public Website Content
@router.get("/classes", response_model=List[ClassResponse])
def get_public_classes(db: Session = Depends(get_db)):
    return db.query(Class).all()


@router.get("/news", response_model=List[NewsResponse])
def get_news(db: Session = Depends(get_db)):
    return db.query(News).order_by(News.published_date.desc()).all()


@router.get("/job-categories", response_model=List[JobCategoryResponse])
def get_job_categories(db: Session = Depends(get_db)):
    return db.query(JobCategory).all()


@router.get("/leadership", response_model=List[LeadershipMemberResponse])
def get_leadership(db: Session = Depends(get_db)):
    return db.query(LeadershipMember).order_by(LeadershipMember.display_order).all()


@router.get("/subjects", response_model=List[SubjectResponse])
def get_subjects(db: Session = Depends(get_db)):
    return db.query(Subject).all()


@router.get("/config", response_model=SchoolConfigResponse)
def get_school_config(db: Session = Depends(get_db)):
    config = db.query(SchoolConfig).first()
    if not config:
        # Create a default config if none exists
        config = SchoolConfig(
            is_admission_open=False,
            admission_deadline=None,
            application_deadlines=[],
            required_documents=[],
            contact_email=None,
            contact_phone=None,
            interview_location=None,
            interview_time_range=None,
            challan_due_days=7,
            admission_fee=0,
            tuition_fee_base=0,
            google_form_link=None,
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


# Application Submissions
@router.post("/apply/student", response_model=StudentApplicationResponse)
async def apply_student(
    first_name: str = Form(...),
    last_name: str = Form(...),
    gender: str = Form(...),
    date_of_birth: str = Form(...),
    b_form_number: str = Form(...),
    guardian_name: str = Form(...),
    guardian_cnic: str = Form(...),
    guardian_phone: str = Form(...),
    guardian_email: str = Form(...),
    city: str = Form(...),
    address: str = Form(...),
    applying_for_class: str = Form(...),
    group_id: Optional[str] = Form(None),
    previous_school: Optional[str] = Form(None),
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # Check if registration is open
    config = db.query(SchoolConfig).first()
    if not config or not config.is_admission_open:
        raise HTTPException(
            status_code=400,
            detail="Admission is currently closed. Please check back later.",
        )

    # Check deadline
    if config.admission_deadline:
        try:
            deadline_dt = datetime.strptime(config.admission_deadline, "%Y-%m-%d")
            if datetime.utcnow() > deadline_dt:
                raise HTTPException(
                    status_code=400, detail="The admission deadline has passed."
                )
        except ValueError:
            pass  # Ignore if deadline format is invalid

    # Check for duplicate applications using Student B-Form/CNIC
    if b_form_number:
        existing_by_bform = (
            db.query(StudentApplication)
            .filter(StudentApplication.b_form_number == b_form_number)
            .first()
        )
        if existing_by_bform:
            status_display = existing_by_bform.status.value.capitalize()
            raise HTTPException(
                status_code=409,
                detail=f"You have already submitted an application with this B-Form/CNIC number. Your current application status is: {status_display}. Please use your Registration ID: {existing_by_bform.regId} to check your application status.",
            )

    # Save photo
    photo_filename = f"{uuid.uuid4()}_{photo.filename}"
    photo_path = os.path.join(settings.UPLOAD_DIR, "photos", photo_filename)
    with open(photo_path, "wb") as buffer:
        shutil.copyfileobj(photo.file, buffer)

    # Generate RegID (simplified for now: REG-timestamp)
    reg_id = f"REG-{int(datetime.utcnow().timestamp())}"

    new_app = StudentApplication(
        regId=reg_id,
        first_name=first_name,
        last_name=last_name,
        gender=gender,
        date_of_birth=date_of_birth,
        student_photo_url=f"/uploads/photos/{photo_filename}",
        b_form_number=b_form_number,
        guardian_name=guardian_name,
        guardian_cnic=guardian_cnic,
        guardian_phone=guardian_phone,
        guardian_email=guardian_email,
        city=city,
        address=address,
        applying_for_class=applying_for_class,
        group_id=uuid.UUID(group_id) if group_id else None,
        previous_school=previous_school,
        status=StudentApplicationStatus.applied,
    )
    db.add(new_app)
    db.commit()
    db.refresh(new_app)
    return new_app


@router.post("/apply/employee", response_model=EmployeeApplicationResponse)
async def apply_employee(
    first_name: str = Form(...),
    last_name: str = Form(...),
    gender: str = Form(...),
    date_of_birth: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    cnic: str = Form(...),
    position_applied_for: str = Form(...),
    subject: Optional[str] = Form(None),
    subjects: Optional[str] = Form(None),  # Comma-separated subject IDs
    highest_qualification: str = Form(...),
    experience_years: str = Form(...),
    current_organization: Optional[str] = Form(None),
    cv: UploadFile = File(...),
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # Check for duplicate applications using CNIC
    existing_application = (
        db.query(EmployeeApplication).filter(EmployeeApplication.cnic == cnic).first()
    )

    if existing_application:
        raise HTTPException(
            status_code=409,
            detail=f"An application has already been submitted with this CNIC number. Your previous application status is: {existing_application.status.value}",
        )

    # Save CV
    cv_filename = f"{uuid.uuid4()}_{cv.filename}"
    cv_path = os.path.join(settings.UPLOAD_DIR, "cvs", cv_filename)
    with open(cv_path, "wb") as buffer:
        shutil.copyfileobj(cv.file, buffer)

    # Save Photo
    photo_filename = f"{uuid.uuid4()}_{photo.filename}"
    photo_path = os.path.join(settings.UPLOAD_DIR, "photos", photo_filename)
    with open(photo_path, "wb") as buffer:
        shutil.copyfileobj(photo.file, buffer)

    new_app = EmployeeApplication(
        first_name=first_name,
        last_name=last_name,
        gender=gender,
        date_of_birth=date_of_birth,
        phone=phone,
        email=email,
        cnic=cnic,
        position_applied_for=position_applied_for,
        subject=subject,
        subjects=subjects,  # Store subject IDs
        highest_qualification=highest_qualification,
        experience_years=experience_years,
        current_organization=current_organization,
        cv_url=f"/uploads/cvs/{cv_filename}",
        photo_url=f"/uploads/photos/{photo_filename}",
        status=EmployeeApplicationStatus.applied,
    )
    db.add(new_app)
    db.commit()
    db.refresh(new_app)
    return new_app
