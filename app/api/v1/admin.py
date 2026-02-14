from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    Form,
    Body,
)
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Any
import uuid
import pandas as pd
from datetime import datetime
import io
import os
import shutil

from app.core.database import get_db
from app.models import (
    StudentApplication,
    EmployeeApplication,
    SchoolConfig,
    News,
    JobCategory,
    JobPosition,
    LeadershipMember,
    EnrolledStudent,
    EnrolledEmployee,
    FeePayment,
)
from app.models.applications import StudentApplicationStatus, EmployeeApplicationStatus
from app.models.auth import User
from app.models.users import UserRole
from app.core import security
from app.schemas import (
    StudentApplicationCreate,
    StudentApplicationUpdate,
    StudentApplicationResponse,
    EmployeeApplicationCreate,
    EmployeeApplicationResponse,
    FeePaymentBase,
    FeePaymentResponse,
    NewsResponse,
    JobCategoryResponse,
    JobPositionResponse,
    LeadershipMemberResponse,
    SchoolConfigBase,
    SchoolConfigResponse,
)
from app.schemas.users import (
    EnrolledStudentUpdate,
    EnrolledStudentResponse,
    EnrolledEmployeeUpdate,
    EnrolledEmployeeResponse,
    EnrolledEmployeeCreate,
)
from app.core.config import settings

from app.schemas.lms import (
    ClassCreate,
    ClassResponse,
    SectionCreate,
    SectionResponse,
    SubjectCreate,
    SubjectResponse,
    ClassSubjectCreate,
    ClassSubjectResponse,
    AttendanceCreate,
    AttendanceResponse,
    BulkSectionCreate,
    BulkMappingCreate,
    BulkClassCreate,
)
from app.schemas.dashboard import (
    DashboardOverviewResponse,
    DashboardStatsResponse,
    ActivityItem,
)
from app.models.lms import Class, Section, Subject, ClassSubject, AttendanceRecord

router = APIRouter()


@router.get("/dashboard/overview", response_model=DashboardOverviewResponse)
def get_dashboard_overview(db: Session = Depends(get_db)):
    # 1. Stats
    student_applications = db.query(StudentApplication).count()
    total_students_enrolled = db.query(EnrolledStudent).count()
    employee_applications = db.query(EmployeeApplication).count()
    total_employees = db.query(EnrolledEmployee).count()

    stats = DashboardStatsResponse(
        student_applications=student_applications,
        total_students_enrolled=total_students_enrolled,
        employee_applications=employee_applications,
        total_employees=total_employees,
        student_app_trend="+0%",
        student_enrolled_trend="+0%",
        employee_app_trend="+0%",
        employee_trend="+0%",
    )

    # 2. Recent Activity (Last 5 items from applications and enrollments)
    recent_activity = []

    # New Student Applications
    latest_apps = (
        db.query(StudentApplication)
        .order_by(StudentApplication.applied_at.desc())
        .limit(5)
        .all()
    )
    for app in latest_apps:
        recent_activity.append(
            ActivityItem(
                id=str(app.id),
                type="application",
                title="New Student Application",
                description=f"{app.first_name} {app.last_name} applied for {app.applying_for_class}",
                timestamp=app.applied_at,
            )
        )

    # Recent Enrollments
    latest_enrolls = (
        db.query(EnrolledStudent)
        .order_by(EnrolledStudent.enrolled_at.desc())
        .limit(5)
        .all()
    )
    for enroll in latest_enrolls:
        recent_activity.append(
            ActivityItem(
                id=str(enroll.id),
                type="enrollment",
                title="Student Enrolled",
                description=f"{enroll.first_name} {enroll.last_name} officially enrolled.",
                timestamp=enroll.enrolled_at,
            )
        )

    # Sort and limit
    recent_activity.sort(key=lambda x: x.timestamp, reverse=True)
    recent_activity = recent_activity[:8]

    # 3. Enrollment Chart (Last 12 months)
    enrollment_chart = []
    for i in range(12):
        # Calculate month
        month_offset = -i
        target_date = datetime.utcnow().month + month_offset
        year_offset = 0
        if target_date <= 0:
            target_date += 12
            year_offset = -1
        elif target_date > 12:
            target_date -= 12
            year_offset = 1

        target_year = datetime.utcnow().year + year_offset
        month_name = datetime(target_year, target_date, 1).strftime("%b")

        # Count enrollments for this month
        count = (
            db.query(EnrolledStudent)
            .filter(
                func.extract("year", EnrolledStudent.enrolled_at) == target_year,
                func.extract("month", EnrolledStudent.enrolled_at) == target_date,
            )
            .count()
        )
        enrollment_chart.append({"month": month_name, "count": count})

    # Reverse to show oldest first
    enrollment_chart = list(reversed(enrollment_chart))

    return {
        "stats": stats,
        "recent_activity": recent_activity,
        "enrollment_chart": enrollment_chart,
    }


# --- LMS & Academic Endpoints ---


# Classes
@router.get("/lms/classes", response_model=List[ClassResponse])
def get_classes(db: Session = Depends(get_db)):
    return db.query(Class).all()


@router.post("/lms/classes", response_model=ClassResponse)
def create_class(class_in: ClassCreate, db: Session = Depends(get_db)):
    cls = Class(**class_in.model_dump())
    db.add(cls)
    db.commit()
    db.refresh(cls)
    return cls


@router.patch("/lms/classes/{class_id}", response_model=ClassResponse)
def update_class(
    class_id: uuid.UUID, class_in: ClassCreate, db: Session = Depends(get_db)
):
    cls = db.query(Class).filter(Class.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    update_data = class_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(cls, field, value)
    db.commit()
    db.refresh(cls)
    return cls


@router.delete("/lms/classes/{class_id}")
def delete_class(class_id: uuid.UUID, db: Session = Depends(get_db)):
    cls = db.query(Class).filter(Class.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    db.delete(cls)
    db.commit()
    return {"message": "Class deleted successfully"}


@router.post("/lms/classes/bulk", response_model=List[ClassResponse])
def create_classes_bulk(bulk_in: BulkClassCreate, db: Session = Depends(get_db)):
    created_classes = []
    for cls_data in bulk_in.classes:
        query = db.query(Class).filter(Class.name == cls_data.name)
        if cls_data.group:
            query = query.filter(Class.group == cls_data.group)
        exists = query.first()
        if not exists:
            new_cls = Class(**cls_data.model_dump())
            db.add(new_cls)
            created_classes.append(new_cls)
    db.commit()
    for cls in created_classes:
        db.refresh(cls)
    return created_classes


# Sections
@router.get("/lms/sections", response_model=List[SectionResponse])
def get_all_sections(db: Session = Depends(get_db)):
    return db.query(Section).all()


@router.post("/lms/sections", response_model=SectionResponse)
def create_section(section_in: SectionCreate, db: Session = Depends(get_db)):
    sec = Section(**section_in.model_dump())
    db.add(sec)
    db.commit()
    db.refresh(sec)
    return sec


@router.post("/lms/sections/bulk", response_model=List[SectionResponse])
def create_sections_bulk(bulk_in: BulkSectionCreate, db: Session = Depends(get_db)):
    sections = []
    for section_data in bulk_in.sections:
        # Check for duplicate section name within the class
        existing_section = (
            db.query(Section)
            .filter(
                Section.class_id == bulk_in.class_id, Section.name == section_data.name
            )
            .first()
        )

        if existing_section:
            # Skip existing sections silently as per the bulk logic seen elsewhere
            continue

        sec = Section(
            name=section_data.name,
            class_id=bulk_in.class_id,
            capacity=section_data.capacity,
        )
        db.add(sec)
        sections.append(sec)

    db.commit()
    for sec in sections:
        db.refresh(sec)
    return sections


@router.get("/lms/classes/{class_id}/sections", response_model=List[SectionResponse])
def get_sections(class_id: uuid.UUID, db: Session = Depends(get_db)):
    return db.query(Section).filter(Section.class_id == class_id).all()


# Subjects
@router.get("/lms/subjects", response_model=List[SubjectResponse])
def get_subjects(db: Session = Depends(get_db)):
    return db.query(Subject).all()


@router.post("/lms/subjects", response_model=SubjectResponse)
def create_subject(subject_in: SubjectCreate, db: Session = Depends(get_db)):
    sub = Subject(**subject_in.model_dump())
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


# Class Subjects (Mapping)
@router.post("/lms/class-subjects", response_model=ClassSubjectResponse)
def assign_subject_to_class(
    mapping_in: ClassSubjectCreate, db: Session = Depends(get_db)
):
    mapping = ClassSubject(**mapping_in.model_dump())
    db.add(mapping)
    db.commit()
    db.refresh(mapping)
    return mapping


@router.post("/lms/class-subjects/bulk", response_model=List[ClassSubjectResponse])
def assign_subjects_to_class_bulk(
    bulk_in: BulkMappingCreate, db: Session = Depends(get_db)
):
    mappings = []
    for mapping_data in bulk_in.mappings:
        existing_mapping = (
            db.query(ClassSubject)
            .filter(
                ClassSubject.class_id == bulk_in.class_id,
                ClassSubject.subject_id == mapping_data.subject_id,
            )
            .first()
        )
        if existing_mapping:
            if mapping_data.teacher_id:
                existing_mapping.teacher_id = mapping_data.teacher_id
                mappings.append(existing_mapping)
        else:
            new_mapping = ClassSubject(
                class_id=bulk_in.class_id,
                subject_id=mapping_data.subject_id,
                teacher_id=mapping_data.teacher_id,
            )
            db.add(new_mapping)
            mappings.append(new_mapping)
    db.commit()
    for m in mappings:
        db.refresh(m)
    return mappings


@router.get(
    "/lms/classes/{class_id}/subjects", response_model=List[ClassSubjectResponse]
)
def get_class_subjects(class_id: uuid.UUID, db: Session = Depends(get_db)):
    return db.query(ClassSubject).filter(ClassSubject.class_id == class_id).all()


@router.patch("/lms/class-subjects/{mapping_id}", response_model=ClassSubjectResponse)
def update_class_subject(
    mapping_id: uuid.UUID,
    data: dict = Body(...),
    db: Session = Depends(get_db),
):
    mapping = db.query(ClassSubject).filter(ClassSubject.id == mapping_id).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")

    if "teacher_id" in data:
        mapping.teacher_id = data["teacher_id"]

    db.commit()
    db.refresh(mapping)
    return mapping


@router.delete("/lms/class-subjects/{mapping_id}")
def delete_class_subject(mapping_id: uuid.UUID, db: Session = Depends(get_db)):
    mapping = db.query(ClassSubject).filter(ClassSubject.id == mapping_id).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")

    db.delete(mapping)
    db.commit()
    return {"message": "Subject unassigned from class"}


# --- Student Application Management ---


@router.get("/student-applications")
def get_student_applications(db: Session = Depends(get_db)):
    return db.query(StudentApplication).all()


@router.patch("/student-applications/{app_id}/review")
def review_student_application(app_id: uuid.UUID, db: Session = Depends(get_db)):
    application = (
        db.query(StudentApplication).filter(StudentApplication.id == app_id).first()
    )
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    application.status = StudentApplicationStatus.reviewed
    application.reviewed_at = datetime.utcnow()
    db.commit()
    return {"message": "Application marked as reviewed."}


@router.patch("/student-applications/{app_id}/pending-verification")
def mark_pending_verification(app_id: uuid.UUID, db: Session = Depends(get_db)):
    application = (
        db.query(StudentApplication).filter(StudentApplication.id == app_id).first()
    )
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    application.status = StudentApplicationStatus.pending_verification
    db.commit()
    return {"message": "Application marked as pending verification."}


@router.patch("/student-applications/{app_id}/reject")
def reject_student_application(app_id: uuid.UUID, db: Session = Depends(get_db)):
    application = (
        db.query(StudentApplication).filter(StudentApplication.id == app_id).first()
    )
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    application.status = StudentApplicationStatus.rejected
    db.commit()
    return {"message": "Application rejected."}


@router.post("/student-applications/{app_id}/enroll")
def enroll_student(
    app_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    application = (
        db.query(StudentApplication).filter(StudentApplication.id == app_id).first()
    )
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # 1. Find Class
    # The application stores class name as string (e.g. "Class 9")
    target_class = (
        db.query(Class).filter(Class.name == application.applying_for_class).first()
    )
    if not target_class:
        # Fallback to code
        target_class = (
            db.query(Class).filter(Class.code == application.applying_for_class).first()
        )

    if not target_class:
        raise HTTPException(
            status_code=400,
            detail=f"Class '{application.applying_for_class}' not found in academic structure. Please create it first.",
        )

    # 2. Find Available Section
    available_section = None
    for section in target_class.sections:
        current_count = (
            db.query(EnrolledStudent)
            .filter(EnrolledStudent.section_id == section.id)
            .count()
        )
        if current_count < (section.capacity or 30):
            available_section = section
            break

    if not available_section:
        raise HTTPException(
            status_code=400,
            detail=f"All sections for {application.applying_for_class} are at full capacity.",
        )

    # 2.5 Check if already enrolled
    if application.status == StudentApplicationStatus.accepted:
        # Check if really in enrolled_students to be safe
        existing_student = (
            db.query(EnrolledStudent)
            .filter(EnrolledStudent.reg_id == application.regId)
            .first()
        )
        if existing_student:
            return {
                "message": "Student is already enrolled",
                "student_id": existing_student.system_student_id,
                "lms_login": existing_student.lms_login,
                "email": existing_student.lms_email,
                "assigned_section": "Already Assigned",
            }

    # 3. Process Enrollment
    year = datetime.utcnow().year
    count = (
        db.query(EnrolledStudent)
        .filter(func.extract("year", EnrolledStudent.enrolled_at) == year)
        .count()
        + 1
    )
    sys_id = f"STU-{year}-{count:03d}"
    adm_num = f"{settings.SCHOOL_NAME_ABBR}-{year}-{uuid.uuid4().hex[:3].upper()}"

    lms_login = sys_id
    lms_password_plain = f"{settings.SCHOOL_NAME_ABBR}@{sys_id}"
    student_email = f"{sys_id}@school.com"

    # Create User Account
    user = User(
        email=student_email,
        password_hash=security.get_password_hash(lms_password_plain),
        role=UserRole.student,
        is_active=True,
    )
    db.add(user)
    db.flush()

    new_student = EnrolledStudent(
        reg_id=application.regId,
        system_student_id=sys_id,
        admission_number=adm_num,
        first_name=application.first_name,
        last_name=application.last_name,
        gender=application.gender,
        date_of_birth=application.date_of_birth,
        student_photo_url=application.student_photo_url,
        b_form_number=application.b_form_number or "N/A",  # Use from application
        guardian_name=application.guardian_name,
        guardian_cnic=application.guardian_cnic,
        guardian_phone=application.guardian_phone,
        guardian_email=application.guardian_email,
        class_id=target_class.id,
        section_id=available_section.id,
        applying_for_class=application.applying_for_class,
        city=application.city,
        address=application.address,
        lms_email=student_email,
        lms_login=lms_login,
        lms_password=lms_password_plain,  # Storing plain password in student record for admin reference as per request
        user_id=user.id,
        is_active=True,
    )

    application.status = StudentApplicationStatus.accepted
    db.add(new_student)
    db.commit()

    return {
        "message": "Student enrolled successfully",
        "student_id": sys_id,
        "lms_login": lms_login,
        "lms_password_plain": lms_password_plain,  # Return to frontend for email
        "email": student_email,
        "assigned_section": available_section.name,
    }


# --- Employee Application Management ---


@router.get("/employee-applications")
def get_employee_applications(db: Session = Depends(get_db)):
    return db.query(EmployeeApplication).all()


@router.post("/employee-applications/{app_id}/interview")
def call_for_interview(
    app_id: uuid.UUID,
    date: str,
    time: str,
    location: str,
    notes: str = "",
    db: Session = Depends(get_db),
):
    application = (
        db.query(EmployeeApplication).filter(EmployeeApplication.id == app_id).first()
    )
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Save interview details
    application.interview_date = date
    application.interview_time = time
    application.interview_location = location
    application.interview_notes = notes
    application.status = EmployeeApplicationStatus.shortlisted

    db.commit()
    db.refresh(application)

    return {
        "message": "Interview invitation recorded.",
        "interview_date": application.interview_date,
        "interview_time": application.interview_time,
        "interview_location": application.interview_location,
    }


@router.patch("/employee-applications/{app_id}/reject")
def reject_employee_application(app_id: uuid.UUID, db: Session = Depends(get_db)):
    application = (
        db.query(EmployeeApplication).filter(EmployeeApplication.id == app_id).first()
    )
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    application.status = EmployeeApplicationStatus.rejected
    db.commit()
    return {"message": "Application rejected."}


@router.post("/employee-applications/{app_id}/hire")
def hire_employee(
    app_id: uuid.UUID,
    employee_type: str,
    functional_role: str,
    system_role: str,
    db: Session = Depends(get_db),
):
    application = (
        db.query(EmployeeApplication).filter(EmployeeApplication.id == app_id).first()
    )
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    year = datetime.utcnow().year
    count = (
        db.query(EnrolledEmployee)
        .filter(func.extract("year", EnrolledEmployee.joined_at) == year)
        .count()
        + 1
    )
    emp_id = f"EMP-{year}-{count:03d}"
    lms_login = emp_id
    lms_password_plain = f"{settings.SCHOOL_NAME_ABBR}@{emp_id}"
    employee_email = application.email

    # 1. Create User Account
    user = User(
        email=employee_email,
        password_hash=security.get_password_hash(lms_password_plain),
        role=UserRole(system_role),
        is_active=True,
    )
    db.add(user)
    db.flush()

    new_employee = EnrolledEmployee(
        employee_id=emp_id,
        first_name=application.first_name,
        last_name=application.last_name,
        gender=application.gender,
        date_of_birth=application.date_of_birth,
        photo_url=application.photo_url,
        phone=application.phone,
        email=application.email,
        cnic=application.cnic,
        employee_type=employee_type,
        functional_role=functional_role,
        system_role=system_role,
        subject=application.subject,
        highest_qualification=application.highest_qualification,
        experience_years=application.experience_years,
        current_organization=application.current_organization,
        cv_url=application.cv_url,
        lms_email=employee_email,
        lms_login=lms_login,
        lms_password=lms_password_plain,
        user_id=user.id,
        is_active=True,
    )
    application.status = EmployeeApplicationStatus.hired
    db.add(new_employee)
    db.commit()
    return {
        "message": "Employee hired and enrolled successfully",
        "employee_id": emp_id,
        "lms_login": lms_login,
        "lms_password_plain": lms_password_plain,
    }


@router.post("/enroll-employee-manual", response_model=EnrolledEmployeeResponse)
def enroll_employee_manual(
    first_name: str = Form(...),
    last_name: str = Form(...),
    gender: str = Form(...),
    date_of_birth: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    cnic: str = Form(...),
    employee_type: str = Form(...),
    functional_role: str = Form(...),
    system_role: str = Form(...),
    subject: Optional[str] = Form(None),
    highest_qualification: str = Form(...),
    experience_years: str = Form(...),
    current_organization: Optional[str] = Form(None),
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    year = datetime.utcnow().year
    count = (
        db.query(EnrolledEmployee)
        .filter(func.extract("year", EnrolledEmployee.joined_at) == year)
        .count()
        + 1
    )
    emp_id = f"EMP-{year}-{count:03d}"
    lms_login = emp_id
    lms_password_plain = f"{settings.SCHOOL_NAME_ABBR}@{emp_id}"
    employee_email = email

    # 0. Save photo
    photo_filename = f"emp_{uuid.uuid4()}_{photo.filename}"
    photo_path = os.path.join(settings.UPLOAD_DIR, "photos", photo_filename)
    with open(photo_path, "wb") as buffer:
        shutil.copyfileobj(photo.file, buffer)

    # 1. Create User Account
    user = User(
        email=employee_email,
        password_hash=security.get_password_hash(lms_password_plain),
        role=UserRole(system_role),
        is_active=True,
    )
    db.add(user)
    db.flush()

    new_employee = EnrolledEmployee(
        employee_id=emp_id,
        first_name=first_name,
        last_name=last_name,
        gender=gender,
        date_of_birth=date_of_birth,
        photo_url=f"/uploads/photos/{photo_filename}",
        phone=phone,
        email=email,
        cnic=cnic,
        employee_type=employee_type,
        functional_role=functional_role,
        system_role=system_role,
        subject=subject,
        highest_qualification=highest_qualification,
        experience_years=experience_years,
        current_organization=current_organization,
        cv_url="#",  # Placeholder since manual doesn't upload CV
        lms_email=employee_email,
        lms_login=lms_login,
        lms_password=lms_password_plain,
        user_id=user.id,
        is_active=True,
    )
    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)
    return new_employee


@router.post("/enroll-student-manual", response_model=EnrolledStudentResponse)
def enroll_student_manual(
    first_name: str = Form(...),
    last_name: str = Form(...),
    gender: str = Form(...),
    date_of_birth: str = Form(...),
    guardian_name: str = Form(...),
    guardian_cnic: str = Form(...),
    guardian_phone: str = Form(...),
    guardian_email: str = Form(...),
    b_form_number: str = Form(...),
    student_cnic: Optional[str] = Form(None),
    applying_for_class: str = Form(...),
    city: str = Form(...),
    address: str = Form(...),
    previous_school: Optional[str] = Form(None),
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # 1. Find Class
    target_class = db.query(Class).filter(Class.name == applying_for_class).first()
    if not target_class:
        target_class = db.query(Class).filter(Class.code == applying_for_class).first()

    if not target_class:
        raise HTTPException(
            status_code=400,
            detail=f"Class '{applying_for_class}' not found. Please create it in Academic Section first.",
        )

    # 2. Find Available Section
    available_section = None
    for section in target_class.sections:
        current_count = (
            db.query(EnrolledStudent)
            .filter(EnrolledStudent.section_id == section.id)
            .count()
        )
        if current_count < (section.capacity or 30):
            available_section = section
            break

    if not available_section:
        raise HTTPException(
            status_code=400,
            detail=f"All sections for {applying_for_class} are full.",
        )

    year = datetime.utcnow().year
    count = (
        db.query(EnrolledStudent)
        .filter(func.extract("year", EnrolledStudent.enrolled_at) == year)
        .count()
        + 1
    )
    sys_id = f"STU-{year}-{count:03d}"
    adm_num = f"{settings.SCHOOL_NAME_ABBR}-{year}-{uuid.uuid4().hex[:3].upper()}"

    lms_login = sys_id
    lms_password_plain = f"{settings.SCHOOL_NAME_ABBR}@{sys_id}"
    student_email = f"{sys_id}@school.com"

    # 0. Save photo
    photo_filename = f"stu_{uuid.uuid4()}_{photo.filename}"
    photo_path = os.path.join(settings.UPLOAD_DIR, "photos", photo_filename)
    with open(photo_path, "wb") as buffer:
        shutil.copyfileobj(photo.file, buffer)

    # 1. Create User Account
    user = User(
        email=student_email,
        password_hash=security.get_password_hash(lms_password_plain),
        role=UserRole.student,
        is_active=True,
    )
    db.add(user)
    db.flush()

    new_student = EnrolledStudent(
        system_student_id=sys_id,
        admission_number=adm_num,
        first_name=first_name,
        last_name=last_name,
        gender=gender,
        date_of_birth=date_of_birth,
        student_photo_url=f"/uploads/photos/{photo_filename}",
        b_form_number=b_form_number,
        student_cnic=student_cnic,
        guardian_name=guardian_name,
        guardian_cnic=guardian_cnic,
        guardian_phone=guardian_phone,
        guardian_email=guardian_email,
        class_id=target_class.id,
        section_id=available_section.id,
        applying_for_class=applying_for_class,
        city=city,
        address=address,
        lms_email=student_email,
        lms_login=lms_login,
        lms_password=lms_password_plain,
        user_id=user.id,
        is_active=True,
    )

    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student


# --- Enrolled Student Management ---


@router.get("/enrolled-students", response_model=List[EnrolledStudentResponse])
def get_enrolled_students(db: Session = Depends(get_db)):
    return db.query(EnrolledStudent).all()


@router.patch("/enrolled-students/{student_id}", response_model=EnrolledStudentResponse)
def update_enrolled_student(
    student_id: uuid.UUID,
    student_data: EnrolledStudentUpdate,
    db: Session = Depends(get_db),
):
    student = db.query(EnrolledStudent).filter(EnrolledStudent.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    update_dict = student_data.model_dump(exclude_unset=True)

    # Handle User account updates if credentials changed
    if "lms_password" in update_dict or "lms_email" in update_dict:
        user = db.query(User).filter(User.id == student.user_id).first()
        if user:
            if "lms_password" in update_dict:
                user.password_hash = security.get_password_hash(
                    update_dict["lms_password"]
                )
            if "lms_email" in update_dict:
                user.email = update_dict["lms_email"]
            db.add(user)

    for key, value in update_dict.items():
        setattr(student, key, value)

    db.commit()
    db.refresh(student)
    return student


@router.delete("/enrolled-students/{student_id}")
def delete_enrolled_student(student_id: uuid.UUID, db: Session = Depends(get_db)):
    student = db.query(EnrolledStudent).filter(EnrolledStudent.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Optionally delete linked user account
    if student.user_id:
        user = db.query(User).filter(User.id == student.user_id).first()
        if user:
            db.delete(user)

    db.delete(student)
    db.commit()
    return {"message": "Student deleted successfully"}


# --- Enrolled Employee Management ---


@router.get("/enrolled-employees", response_model=List[EnrolledEmployeeResponse])
def get_enrolled_employees(db: Session = Depends(get_db)):
    return db.query(EnrolledEmployee).all()


@router.get(
    "/enrolled-employees/{employee_id}", response_model=EnrolledEmployeeResponse
)
def get_enrolled_employee(employee_id: uuid.UUID, db: Session = Depends(get_db)):
    employee = (
        db.query(EnrolledEmployee).filter(EnrolledEmployee.id == employee_id).first()
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@router.patch(
    "/enrolled-employees/{employee_id}", response_model=EnrolledEmployeeResponse
)
def update_enrolled_employee(
    employee_id: uuid.UUID,
    employee_data: EnrolledEmployeeUpdate,
    db: Session = Depends(get_db),
):
    employee = (
        db.query(EnrolledEmployee).filter(EnrolledEmployee.id == employee_id).first()
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    for key, value in employee_data.model_dump(exclude_unset=True).items():
        setattr(employee, key, value)
    db.commit()
    db.refresh(employee)
    return employee


@router.delete("/enrolled-employees/{employee_id}")
def remove_enrolled_employee(employee_id: uuid.UUID, db: Session = Depends(get_db)):
    employee = (
        db.query(EnrolledEmployee).filter(EnrolledEmployee.id == employee_id).first()
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Delete linked user account
    if employee.user_id:
        user = db.query(User).filter(User.id == employee.user_id).first()
        if user:
            db.delete(user)

    db.delete(employee)
    db.commit()
    return {"message": "Employee removed successfully"}


@router.post("/users/bulk-enroll")
async def bulk_enroll(
    file: UploadFile = File(...), role: str = Form(...), db: Session = Depends(get_db)
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files allowed")
    content = await file.read()
    df = pd.read_csv(io.BytesIO(content))
    year = datetime.utcnow().year

    # Fill NaN values for optional fields
    df = df.where(pd.notnull(df), None)

    if role == "student":
        count = (
            db.query(EnrolledStudent)
            .filter(func.extract("year", EnrolledStudent.enrolled_at) == year)
            .count()
        )
        for _, row in df.iterrows():
            count += 1
            sys_id = f"STU-{year}-{count:03d}"
            adm_num = (
                f"{settings.SCHOOL_NAME_ABBR}-{year}-{uuid.uuid4().hex[:3].upper()}"
            )
            lms_login = sys_id
            lms_password_plain = f"{settings.SCHOOL_NAME_ABBR}@{sys_id}"

            # Use guardian_email or a default
            email = (
                row.get("email") or row.get("guardian_email") or f"{sys_id}@school.com"
            )

            # Create User
            user = User(
                email=email,
                password_hash=security.get_password_hash(lms_password_plain),
                role=UserRole.student,
                is_active=True,
            )
            db.add(user)
            db.flush()

            # Automatic Class & Section finding
            applying_class_name = str(row.get("class") or row.get("applying_for_class"))
            target_class = (
                db.query(Class).filter(Class.name == applying_class_name).first()
            )
            if not target_class:
                target_class = (
                    db.query(Class).filter(Class.code == applying_class_name).first()
                )

            if not target_class:
                continue  # Skip if class not found

            available_section = None
            for section in target_class.sections:
                curr_cnt = (
                    db.query(EnrolledStudent)
                    .filter(EnrolledStudent.section_id == section.id)
                    .count()
                )
                if curr_cnt < (section.capacity or 30):
                    available_section = section
                    break

            if not available_section:
                continue  # Skip if no section available

            student = EnrolledStudent(
                system_student_id=sys_id,
                admission_number=adm_num,
                first_name=row["first_name"],
                last_name=row["last_name"],
                gender=row.get("gender", "Other"),
                date_of_birth=str(row["date_of_birth"]),
                b_form_number=str(row.get("b_form_number", "N/A")),
                guardian_name=row["guardian_name"],
                guardian_cnic=str(row.get("guardian_cnic", "N/A")),
                guardian_phone=str(row.get("guardian_phone", "N/A")),
                guardian_email=str(row.get("guardian_email", "N/A")),
                class_id=target_class.id,
                section_id=available_section.id,
                applying_for_class=applying_class_name,
                lms_email=email,
                lms_login=lms_login,
                lms_password=lms_password_plain,
                user_id=user.id,
                is_active=True,
                student_photo_url=row.get("photo_url"),  # Handle picture from excel
            )
            db.add(student)
    elif role in ["teacher", "staff"]:
        count = (
            db.query(EnrolledEmployee)
            .filter(func.extract("year", EnrolledEmployee.joined_at) == year)
            .count()
        )
        for _, row in df.iterrows():
            count += 1
            emp_id = f"EMP-{year}-{count:03d}"
            lms_login = emp_id
            lms_password_plain = f"{settings.SCHOOL_NAME_ABBR}@{emp_id}"

            # Create User
            user = User(
                email=row["email"],
                password_hash=security.get_password_hash(lms_password_plain),
                role=UserRole(row.get("system_role", role)),
                is_active=True,
            )
            db.add(user)
            db.flush()

            employee = EnrolledEmployee(
                employee_id=emp_id,
                first_name=row["first_name"],
                last_name=row["last_name"],
                gender=row.get("gender", "Other"),
                date_of_birth=str(row["date_of_birth"]),
                phone=str(row["phone"]),
                email=row["email"],
                cnic=str(row["cnic"]),
                employee_type=row.get("employee_type", "teaching"),
                functional_role=row.get("functional_role", "Teacher"),
                system_role=row.get("system_role", role),
                highest_qualification=row.get("highest_qualification", "N/A"),
                experience_years=str(row.get("experience_years", "0")),
                lms_email=row["email"],
                lms_login=emp_id,
                lms_password=lms_password_plain,
                user_id=user.id,
                is_active=True,
                photo_url=row.get("photo_url"),  # Handle picture from excel
            )
            db.add(employee)
    db.commit()
    return {"message": f"Processed {len(df)} entries from CSV."}


# --- Website Content Management ---


@router.options("/config")
def config_options():
    """Handle CORS preflight requests"""
    return {}


@router.post("/config", response_model=SchoolConfigResponse)
def create_config(config_data: SchoolConfigBase, db: Session = Depends(get_db)):
    try:
        # Check if config already exists
        existing_config = db.query(SchoolConfig).first()
        if existing_config:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Configuration already exists. Use PATCH to update existing configuration.",
            )

        # Create new config
        config = SchoolConfig()
        db.add(config)

        # Set fields from the schema
        update_data = config_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(config, key):
                # Convert empty strings to None for optional fields
                if value == "":
                    value = None
                setattr(config, key, value)

        db.commit()
        db.refresh(config)
        return config
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create configuration: {str(e)}",
        )


@router.patch("/config", response_model=SchoolConfigResponse)
def update_config(config_data: SchoolConfigBase, db: Session = Depends(get_db)):
    try:
        config = db.query(SchoolConfig).first()
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Configuration not found. Use POST to create a new configuration.",
            )

        # Update fields from the schema
        update_data = config_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(config, key):
                # Convert empty strings to None for optional fields
                if value == "":
                    value = None
                setattr(config, key, value)

        db.commit()
        db.refresh(config)
        return config
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update configuration: {str(e)}",
        )


# --- Fee & Payment Management ---


@router.get("/fee-payments", response_model=List[FeePaymentResponse])
def get_fee_payments(status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(FeePayment)
    if status:
        query = query.filter(FeePayment.status == status)
    return query.all()


@router.post("/fee-payments", response_model=FeePaymentResponse)
def create_fee_payment(
    payment: FeePaymentBase,
    student_id: Optional[uuid.UUID] = None,
    app_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
):
    db_payment = FeePayment(
        **payment.model_dump(), student_id=student_id, application_id=app_id
    )
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment


@router.patch("/fee-payments/{payment_id}", response_model=FeePaymentResponse)
def update_fee_payment(
    payment_id: uuid.UUID, status: str, db: Session = Depends(get_db)
):
    payment = db.query(FeePayment).filter(FeePayment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")
    payment.status = status
    if status == "paid":
        payment.payment_date = datetime.utcnow()
    db.commit()
    db.refresh(payment)
    return payment


@router.get("/news")
def get_all_news(db: Session = Depends(get_db)):
    return db.query(News).all()


@router.delete("/news/{news_id}")
def delete_news(news_id: int, db: Session = Depends(get_db)):
    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    db.delete(news)
    db.commit()
    return {"message": "News deleted successfully"}


# --- Job Management ---


@router.post("/job-categories")
def create_job_category(
    title: str, description: Optional[str] = None, db: Session = Depends(get_db)
):
    cat = JobCategory(title=title, description=description)
    db.add(cat)
    db.commit()
    return cat


@router.patch("/job-categories/{category_id}")
def update_job_category(
    category_id: uuid.UUID,
    title: Optional[str] = None,
    description: Optional[str] = None,
    db: Session = Depends(get_db),
):
    cat = db.query(JobCategory).filter(JobCategory.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Job category not found")
    if title:
        cat.title = title
    if description:
        cat.description = description
    db.commit()
    return cat


@router.delete("/job-categories/{category_id}")
def delete_job_category(category_id: uuid.UUID, db: Session = Depends(get_db)):
    cat = db.query(JobCategory).filter(JobCategory.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Job category not found")
    db.delete(cat)
    db.commit()
    return {"message": "Job category deleted successfully"}


@router.post("/job-positions")
def create_job_position(
    category_id: uuid.UUID, title: str, db: Session = Depends(get_db)
):
    pos = JobPosition(category_id=category_id, title=title)
    db.add(pos)
    db.commit()
    return pos


@router.patch("/job-positions/{position_id}")
def update_job_position(
    position_id: uuid.UUID,
    title: Optional[str] = None,
    category_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
):
    pos = db.query(JobPosition).filter(JobPosition.id == position_id).first()
    if not pos:
        raise HTTPException(status_code=404, detail="Job position not found")
    if title:
        pos.title = title
    if category_id:
        pos.category_id = category_id
    db.commit()
    return pos


@router.delete("/job-positions/{position_id}")
def delete_job_position(position_id: uuid.UUID, db: Session = Depends(get_db)):
    pos = db.query(JobPosition).filter(JobPosition.id == position_id).first()
    if not pos:
        raise HTTPException(status_code=404, detail="Job position not found")
    db.delete(pos)
    db.commit()
    return {"message": "Job position deleted successfully"}


# --- Leadership Management ---


@router.post("/leadership")
def create_leadership_member(
    name: str = Form(...),
    position: str = Form(...),
    display_order: int = Form(0),
    bio: Optional[str] = Form(None),
    quote: Optional[str] = Form(None),
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    photo_filename = f"lead_{uuid.uuid4()}_{photo.filename}"
    photo_path = os.path.join(settings.UPLOAD_DIR, "photos", photo_filename)
    with open(photo_path, "wb") as buffer:
        shutil.copyfileobj(photo.file, buffer)
    member = LeadershipMember(
        name=name,
        position=position,
        display_order=display_order,
        bio=bio,
        quote=quote,
        image_url=f"/uploads/photos/{photo_filename}",
    )
    db.add(member)
    db.commit()
    return member


@router.patch("/leadership/{member_id}")
def update_leadership_member(
    member_id: uuid.UUID,
    name: Optional[str] = Form(None),
    position: Optional[str] = Form(None),
    display_order: Optional[int] = Form(None),
    bio: Optional[str] = Form(None),
    quote: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    member = db.query(LeadershipMember).filter(LeadershipMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    if name:
        member.name = name
    if position:
        member.position = position
    if display_order is not None:
        member.display_order = display_order
    if bio:
        member.bio = bio
    if quote:
        member.quote = quote
    if photo:
        photo_filename = f"lead_{uuid.uuid4()}_{photo.filename}"
        photo_path = os.path.join(settings.UPLOAD_DIR, "photos", photo_filename)
        with open(photo_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
        member.image_url = f"/uploads/photos/{photo_filename}"
    db.commit()
    return member


@router.delete("/leadership/{member_id}")
def delete_leadership_member(member_id: uuid.UUID, db: Session = Depends(get_db)):
    member = db.query(LeadershipMember).filter(LeadershipMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    db.delete(member)
    db.commit()
    return {"message": "Member deleted successfully"}


# --- News Management ---


@router.post("/news")
def create_news(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    image_url = None
    if photo:
        photo_filename = f"news_{uuid.uuid4()}_{photo.filename}"
        photo_path = os.path.join(settings.UPLOAD_DIR, "photos", photo_filename)
        with open(photo_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
        image_url = f"/uploads/photos/{photo_filename}"
    new_news = News(title=title, description=description, image_url=image_url)
    db.add(new_news)
    db.commit()
    return new_news


@router.patch("/news/{news_id}")
def update_news(
    news_id: int,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    if title:
        news.title = title
    if description:
        news.description = description
    if photo:
        photo_filename = f"news_{uuid.uuid4()}_{photo.filename}"
        photo_path = os.path.join(settings.UPLOAD_DIR, "photos", photo_filename)
        with open(photo_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
        news.image_url = f"/uploads/photos/{photo_filename}"
    db.commit()
    return news
