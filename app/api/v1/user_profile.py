from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

from app.api import deps
from app.models.auth import User
from app.models.users import EnrolledStudent, EnrolledEmployee
from app.models.lms import (
    ClassSubject,
    TeacherSubject,
    StudentSubject,
    Class,
    Subject,
    Section,
)
from pydantic import BaseModel

router = APIRouter()


class UserProfileResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    avatar: Optional[str] = None
    registration_id: str


class AcademicInfoResponse(BaseModel):
    current_class: Optional[str] = None
    section: Optional[str] = None
    subjects: List[dict] = []
    classes: Optional[List[dict]] = None


def get_full_url(path: str) -> str:
    """Convert relative path to full URL"""
    if not path:
        return ""
    if path.startswith("http"):
        return path
    from app.core.config import settings

    return f"http://localhost:8000{path}"


@router.get("/me")
def get_my_profile(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    if current_user.role == "student":
        profile = (
            db.query(EnrolledStudent)
            .filter(EnrolledStudent.user_id == current_user.id)
            .first()
        )
        if not profile:
            return {
                "success": True,
                "message": "Profile retrieved",
                "data": {
                    "id": str(current_user.id),
                    "name": current_user.email.split("@")[0],
                    "email": current_user.email,
                    "role": current_user.role,
                    "registration_id": "ST-NEW",
                },
            }
        return {
            "success": True,
            "message": "Profile retrieved",
            "data": {
                "id": str(current_user.id),
                "name": f"{profile.first_name} {profile.last_name}",
                "email": profile.lms_email or current_user.email,
                "role": current_user.role,
                "avatar": get_full_url(profile.student_photo_url),
                "registration_id": profile.system_student_id,
            },
        }
    else:
        profile = (
            db.query(EnrolledEmployee)
            .filter(EnrolledEmployee.user_id == current_user.id)
            .first()
        )
        if not profile:
            return {
                "success": True,
                "message": "Profile retrieved",
                "data": {
                    "id": str(current_user.id),
                    "name": current_user.email.split("@")[0],
                    "email": current_user.email,
                    "role": current_user.role,
                    "registration_id": "EMP-NEW",
                },
            }
        return {
            "success": True,
            "message": "Profile retrieved",
            "data": {
                "id": str(current_user.id),
                "name": f"{profile.first_name} {profile.last_name}",
                "email": profile.lms_email or current_user.email,
                "role": current_user.role,
                "avatar": get_full_url(profile.photo_url),
                "registration_id": profile.employee_id,
            },
        }


@router.get("/dashboard-auth", response_model=dict)
def verify_dashboard_access(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    """
    Verify user role and return dashboard redirect information.
    Use this endpoint to protect dashboard routes.
    """
    if not current_user.is_active:
        return {
            "success": False,
            "message": "Account is inactive",
            "data": {
                "is_valid": False,
                "role": current_user.role,
                "redirect_to": "/login",
            },
        }

    # Determine correct dashboard based on role
    if current_user.role == "teacher":
        redirect_to = "/lms/teacher/dashboard"
        dashboard_type = "teacher"
    elif current_user.role == "student":
        redirect_to = "/lms/student/dashboard"
        dashboard_type = "student"
    elif current_user.role == "admin":
        redirect_to = "/lms/teacher/dashboard"
        dashboard_type = "admin"
    else:
        redirect_to = "/"
        dashboard_type = "unknown"

    return {
        "success": True,
        "message": "Authentication verified",
        "data": {
            "is_valid": True,
            "role": current_user.role,
            "dashboard_type": dashboard_type,
            "redirect_to": redirect_to,
            "user_id": str(current_user.id),
            "email": current_user.email,
        },
    }


@router.get("/verify-role/{required_role}", response_model=dict)
def verify_role_access(
    required_role: str,
    current_user: User = Depends(deps.get_current_user),
):
    """
    Verify if current user has the required role.
    Use this for route protection on frontend.

    Example: /verify-role/teacher - returns 403 if user is not teacher
    """
    role_mapping = {
        "teacher": ["teacher", "admin"],
        "student": ["student", "admin"],
        "admin": ["admin"],
    }

    allowed_roles = role_mapping.get(required_role, [])

    if current_user.role not in allowed_roles:
        return {
            "success": False,
            "message": f"Access denied. This page requires {required_role} privileges.",
            "data": {
                "has_access": False,
                "current_role": current_user.role,
                "required_role": required_role,
            },
        }

    return {
        "success": True,
        "message": "Access granted",
        "data": {
            "has_access": True,
            "current_role": current_user.role,
            "required_role": required_role,
        },
    }


@router.get("/academic-info")
def get_my_academic_info(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    if current_user.role == "student":
        student = (
            db.query(EnrolledStudent)
            .filter(EnrolledStudent.user_id == current_user.id)
            .first()
        )
        if not student:
            return {"success": True, "message": "No academic info", "data": {}}

        subjects = (
            db.query(ClassSubject)
            .filter(ClassSubject.class_id == student.class_id)
            .all()
        )

        return {
            "success": True,
            "message": "Academic info retrieved",
            "data": {
                "current_class": student.class_.name if student.class_ else "N/A",
                "section": student.section.name if student.section else "N/A",
                "subjects": [
                    {
                        "id": str(cs.id),
                        "name": cs.subject.name,
                        "code": cs.subject.code,
                        "teacher": f"{cs.teacher_subjects[0].teacher.first_name} {cs.teacher_subjects[0].teacher.last_name}"
                        if cs.teacher_subjects and cs.teacher_subjects[0].teacher
                        else "N/A",
                    }
                    for cs in subjects
                ],
            },
        }
    else:
        employee = (
            db.query(EnrolledEmployee)
            .filter(EnrolledEmployee.user_id == current_user.id)
            .first()
        )
        if not employee:
            return AcademicInfoResponse()

        # Get subjects assigned to this teacher
        teacher_subjects = (
            db.query(TeacherSubject)
            .filter(TeacherSubject.teacher_id == employee.id)
            .all()
        )

        # Group subjects by class
        classes_dict = {}
        for ts in teacher_subjects:
            class_id = str(ts.class_.id) if ts.class_ else "unknown"
            class_name = ts.class_.name if ts.class_ else "Unknown Class"

            if class_id not in classes_dict:
                classes_dict[class_id] = {
                    "class_id": class_id,
                    "class_name": class_name,
                    "class_code": ts.class_.code if ts.class_ else "",
                    "subjects": [],
                }

            classes_dict[class_id]["subjects"].append(
                {
                    "id": str(ts.id),
                    "subject_id": str(ts.subject.id) if ts.subject else "",
                    "name": ts.subject.name if ts.subject else "",
                    "code": ts.subject.code if ts.subject else "",
                    "section": ts.section.name if ts.section else "All",
                    "section_id": str(ts.section.id) if ts.section else None,
                }
            )

        # Convert to list sorted by class name
        classes = sorted(classes_dict.values(), key=lambda x: x["class_name"])

        # Also create flat list of subjects for backward compatibility
        subjects_list = []
        for ts in teacher_subjects:
            subjects_list.append(
                {
                    "id": str(ts.id),
                    "name": ts.subject.name if ts.subject else "",
                    "class": ts.class_.name if ts.class_ else "",
                    "section": ts.section.name if ts.section else "All",
                    "code": ts.subject.code if ts.subject else "",
                }
            )

        return {"classes": classes, "subjects": subjects_list}


@router.get("/teacher/classes", response_model=dict)
def get_teacher_classes(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    """Get all classes a teacher teaches with their subjects and student counts"""
    if current_user.role not in ["teacher", "admin"]:
        return {"success": False, "message": "Unauthorized", "data": []}

    employee = (
        db.query(EnrolledEmployee)
        .filter(EnrolledEmployee.user_id == current_user.id)
        .first()
    )
    if not employee:
        return {"success": False, "message": "Employee not found", "data": []}

    # Get all teacher subjects with class info
    teacher_subjects = (
        db.query(TeacherSubject, Class)
        .join(Class, TeacherSubject.class_id == Class.id)
        .filter(TeacherSubject.teacher_id == employee.id)
        .all()
    )

    # Group by class
    classes_dict = {}
    for ts, cls in teacher_subjects:
        class_id = str(cls.id)

        # Get student count for this class
        student_count = (
            db.query(EnrolledStudent).filter(EnrolledStudent.class_id == cls.id).count()
        )

        if class_id not in classes_dict:
            classes_dict[class_id] = {
                "class_id": class_id,
                "class_name": cls.name,
                "class_code": cls.code or "",
                "grade_level": cls.grade_level,
                "subject_count": 0,
                "student_count": student_count,
                "subjects": [],
            }

        # Get subject info from TeacherSubject
        subject = (
            db.query(Subject).filter(Subject.id == ts.subject_id).first()
            if ts.subject_id
            else None
        )
        section = (
            db.query(Section).filter(Section.id == ts.section_id).first()
            if ts.section_id
            else None
        )

        classes_dict[class_id]["subjects"].append(
            {
                "teacher_subject_id": str(ts.id),
                "subject_id": str(ts.subject_id) if ts.subject_id else "",
                "subject_name": subject.name if subject else "",
                "subject_code": subject.code if subject else "",
                "section_id": str(ts.section_id) if ts.section_id else None,
                "section_name": section.name if section else "All Sections",
                "class_subject_id": str(ts.class_subject_id)
                if ts.class_subject_id
                else None,
            }
        )
        classes_dict[class_id]["subject_count"] += 1

    # Convert to sorted list
    classes = sorted(classes_dict.values(), key=lambda x: x["class_name"])

    return {
        "success": True,
        "message": "Classes retrieved successfully",
        "data": classes,
    }


@router.get("/teacher/stats")
def get_teacher_stats(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    """Get dashboard stats for teacher"""
    if current_user.role not in ["teacher", "admin"]:
        return {"success": False, "message": "Unauthorized", "data": {}}

    from app.models.lms import AttendanceRecord, AttendanceStatus
    from datetime import datetime, timedelta

    employee = (
        db.query(EnrolledEmployee)
        .filter(EnrolledEmployee.user_id == current_user.id)
        .first()
    )
    if not employee:
        return {"success": False, "message": "Employee not found", "data": {}}

    # Get all teacher subjects with class info
    teacher_subjects = (
        db.query(TeacherSubject, Class)
        .join(Class, TeacherSubject.class_id == Class.id)
        .filter(TeacherSubject.teacher_id == employee.id)
        .all()
    )

    # Count total unique students across all classes
    class_ids = set()
    for ts, cls in teacher_subjects:
        class_ids.add(cls.id)

    total_students = (
        db.query(EnrolledStudent)
        .filter(EnrolledStudent.class_id.in_(class_ids))
        .count()
    )

    # Count active courses (unique subjects)
    active_courses = len(teacher_subjects)

    # Count classes this week
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    # Get class_subject_ids from teacher_subjects
    class_subject_ids = [
        ts.class_subject_id for ts, _ in teacher_subjects if ts.class_subject_id
    ]

    # Get attendance records for this week
    attendance_records = []
    if class_subject_ids:
        attendance_records = (
            db.query(AttendanceRecord)
            .filter(
                AttendanceRecord.class_subject_id.in_(class_subject_ids),
                AttendanceRecord.date >= start_of_week,
                AttendanceRecord.date <= end_of_week,
            )
            .all()
        )

    classes_this_week = len(set([r.class_subject_id for r in attendance_records]))

    # Calculate average attendance percentage
    total_attendance = len(attendance_records)
    present_count = sum(1 for r in attendance_records if str(r.status) == "present")
    avg_attendance = (
        round((present_count / total_attendance) * 100, 1)
        if total_attendance > 0
        else 0
    )

    return {
        "success": True,
        "message": "Stats retrieved successfully",
        "data": {
            "total_students": total_students,
            "active_courses": active_courses,
            "avg_attendance": avg_attendance,
            "classes_this_week": classes_this_week,
        },
    }


@router.get("/teacher/classes/{class_id}/subjects", response_model=dict)
def get_teacher_class_subjects(
    class_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    """Get all subjects a teacher teaches in a specific class"""
    if current_user.role not in ["teacher", "admin"]:
        return {"success": False, "message": "Unauthorized", "data": []}

    employee = (
        db.query(EnrolledEmployee)
        .filter(EnrolledEmployee.user_id == current_user.id)
        .first()
    )
    if not employee:
        return {"success": False, "message": "Employee not found", "data": []}

    # Get subjects for this class
    teacher_subjects = (
        db.query(TeacherSubject)
        .filter(
            TeacherSubject.teacher_id == employee.id,
            TeacherSubject.class_id == class_id,
        )
        .all()
    )

    subjects = []
    for ts in teacher_subjects:
        # Get student count for this subject
        student_count = (
            db.query(StudentSubject)
            .filter(StudentSubject.class_subject_id == ts.class_subject_id)
            .count()
        )

        subjects.append(
            {
                "teacher_subject_id": str(ts.id),
                "subject_id": str(ts.subject.id) if ts.subject else "",
                "subject_name": ts.subject.name if ts.subject else "",
                "subject_code": ts.subject.code if ts.subject else "",
                "section_id": str(ts.section.id) if ts.section else None,
                "section_name": ts.section.name if ts.section else "All Sections",
                "student_count": student_count,
            }
        )

    return {
        "success": True,
        "message": "Subjects retrieved successfully",
        "data": subjects,
    }


@router.get("/teacher/class/{class_id}", response_model=dict)
def get_class_details(
    class_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    """Get class details for a teacher"""
    if current_user.role not in ["teacher", "admin"]:
        return {"success": False, "message": "Unauthorized", "data": None}

    # Get class info
    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        return {"success": False, "message": "Class not found", "data": None}

    # Get employee
    employee = (
        db.query(EnrolledEmployee)
        .filter(EnrolledEmployee.user_id == current_user.id)
        .first()
    )
    if not employee:
        return {"success": False, "message": "Employee not found", "data": None}

    # Verify teacher teaches this class (check by any subject in this class)
    teacher_subjects_check = (
        db.query(TeacherSubject)
        .filter(
            TeacherSubject.teacher_id == employee.id,
            TeacherSubject.class_id == class_id,
        )
        .first()
    )

    if not teacher_subjects_check and current_user.role != "admin":
        return {"success": False, "message": "You don't teach this class", "data": None}

    # Get all subjects for this class that this teacher teaches
    teacher_subjects = (
        db.query(TeacherSubject)
        .filter(
            TeacherSubject.teacher_id == employee.id,
            TeacherSubject.class_id == class_id,
        )
        .all()
    )

    subjects = []
    for ts in teacher_subjects:
        student_count = (
            db.query(StudentSubject)
            .filter(StudentSubject.class_subject_id == ts.class_subject_id)
            .count()
        )

        subjects.append(
            {
                "teacher_subject_id": str(ts.id),
                "class_subject_id": str(ts.class_subject_id),
                "subject_id": str(ts.subject.id) if ts.subject else "",
                "subject_name": ts.subject.name if ts.subject else "",
                "subject_code": ts.subject.code if ts.subject else "",
                "section_id": str(ts.section.id) if ts.section else None,
                "section_name": ts.section.name if ts.section else "All Sections",
                "student_count": student_count,
            }
        )

    # Get total enrolled students
    total_students = (
        db.query(StudentSubject)
        .filter(StudentSubject.class_id == class_id)
        .distinct(StudentSubject.student_id)
        .count()
    )

    # Get enrolled students list
    enrolled_students = (
        db.query(EnrolledStudent).filter(EnrolledStudent.class_id == class_id).all()
    )

    students_list = []
    for student in enrolled_students:
        students_list.append(
            {
                "id": str(student.id),
                "student_id": str(student.id),
                "first_name": student.first_name,
                "last_name": student.last_name,
                "admission_number": student.admission_number,
                "email": student.lms_email or "",
            }
        )

    # Get assignments count and average grade for this class
    from app.models.lms import Assignment, AssignmentSubmission

    class_subject_ids = [
        s["class_subject_id"] for s in subjects if s.get("class_subject_id")
    ]

    assignments_count = 0
    avg_grade = 0.0
    total_graded = 0
    grade_sum = 0.0

    if class_subject_ids:
        assignments_count = (
            db.query(Assignment)
            .filter(Assignment.class_subject_id.in_(class_subject_ids))
            .count()
        )

        # Get all submissions for these assignments
        submissions = (
            db.query(AssignmentSubmission)
            .filter(
                AssignmentSubmission.assignment_id.in_(
                    db.query(Assignment.id)
                    .filter(Assignment.class_subject_id.in_(class_subject_ids))
                    .subquery()
                ),
                AssignmentSubmission.is_graded == True,
            )
            .all()
        )

        total_graded = len(submissions)
        for sub in submissions:
            try:
                grade_sum += float(sub.grade) if sub.grade else 0
            except:
                pass

        if total_graded > 0:
            avg_grade = round(grade_sum / total_graded, 1)

    return {
        "success": True,
        "message": "Class details retrieved successfully",
        "data": {
            "class_id": str(class_obj.id),
            "class_name": class_obj.name,
            "class_code": class_obj.code,
            "grade_level": class_obj.grade_level,
            "total_students": total_students,
            "subject_count": len(subjects),
            "subjects": subjects,
            "students": students_list,
            "stats": {
                "assignments_count": assignments_count,
                "avg_grade": avg_grade,
                "total_graded": total_graded,
            },
        },
    }


@router.get("/students/class-subject/{class_subject_id}")
def get_students_by_subject(
    class_subject_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    """Get students enrolled in a specific subject"""
    if current_user.role not in ["teacher", "admin", "student"]:
        return {"success": False, "message": "Unauthorized", "data": []}

    # Get students enrolled in this class_subject
    student_subjects = (
        db.query(StudentSubject)
        .filter(StudentSubject.class_subject_id == class_subject_id)
        .all()
    )

    students = []
    for ss in student_subjects:
        student = (
            db.query(EnrolledStudent)
            .filter(EnrolledStudent.id == ss.student_id)
            .first()
        )
        if student:
            students.append(
                {
                    "id": str(student.id),
                    "student_id": str(student.id),
                    "first_name": student.first_name,
                    "last_name": student.last_name,
                    "admission_number": student.admission_number,
                    "email": student.lms_email or "",
                }
            )

    return {
        "success": True,
        "message": "Students retrieved successfully",
        "data": students,
    }

    return {
        "success": True,
        "message": "Students retrieved successfully",
        "data": students,
    }
