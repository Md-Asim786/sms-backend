from typing import List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import uuid
import os
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from collections import defaultdict

from app.api import deps
from app.core.config import settings
from app.models.lms import (
    Class,
    Section,
    Subject,
    ClassSubject,
    AttendanceRecord,
    Assignment,
    AssignmentSubmission,
    Lecture,
    TeacherSubject,
    StudentSubject,
    AttendanceStatus,
)
from app.models.auth import User
from app.models.users import EnrolledStudent
from app.schemas.lms import (
    ClassResponse,
    SectionResponse,
    SubjectResponse,
    ClassSubjectResponse,
    AttendanceCreate,
    AttendanceResponse,
    AttendanceUpdate,
    AttendanceStats,
    BulkAttendanceRequest,
    AssignmentCreate,
    AssignmentUpdate,
    AssignmentResponse,
    AssignmentWithSubmissions,
    AssignmentSubmissionCreate,
    AssignmentSubmissionResponse,
    AssignmentSubmissionUpdate,
    GradeSubmissionRequest,
    LectureCreate,
    LectureUpdate,
    LectureResponse,
    APIResponse,
)

router = APIRouter()


def get_teacher_class_subject_ids(db: Session, teacher_id: uuid.UUID) -> List[uuid.UUID]:
    """Get all class_subject_ids that a teacher teaches"""
    mappings = db.query(TeacherSubject).filter(TeacherSubject.teacher_id == teacher_id).all()
    return [m.class_subject_id for m in mappings]


def verify_teacher_teaches_subject(db: Session, teacher_id: uuid.UUID, class_subject_id: uuid.UUID) -> bool:
    """Verify that a teacher teaches a specific subject"""
    mapping = db.query(TeacherSubject).filter(
        TeacherSubject.teacher_id == teacher_id,
        TeacherSubject.class_subject_id == class_subject_id
    ).first()
    return mapping is not None


def verify_student_enrolled(db: Session, student_id: uuid.UUID, class_subject_id: uuid.UUID) -> bool:
    """Verify that a student is enrolled in a subject"""
    enrollment = db.query(StudentSubject).filter(
        StudentSubject.student_id == student_id,
        StudentSubject.class_subject_id == class_subject_id
    ).first()
    return enrollment is not None


# ==================== ATTENDANCE MODULE ====================

@router.post("/attendance", response_model=APIResponse)
def mark_attendance(
    attendance_in: AttendanceCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.RoleChecker(["teacher", "admin"])),
):
    """Mark attendance for a student (Teacher only)"""
    
    # Prevent future dates
    if attendance_in.date.date() > datetime.now().date():
        return {
            "success": False,
            "message": "Cannot mark attendance for future dates",
            "data": None
        }

    # Prevent duplicates - check if attendance already marked for this student, subject, and date
    existing = db.query(AttendanceRecord).filter(
        AttendanceRecord.student_id == attendance_in.student_id,
        AttendanceRecord.class_subject_id == attendance_in.class_subject_id,
        func.date(AttendanceRecord.date) == attendance_in.date.date(),
    ).first()
    
    if existing:
        return {
            "success": False,
            "message": "Attendance for today is already marked.",
            "data": None
        }

    record = AttendanceRecord(
        student_id=attendance_in.student_id,
        class_subject_id=attendance_in.class_subject_id,
        date=attendance_in.date,
        status=attendance_in.status,
        marked_by_id=current_user.id,
        audit_logs=[{
            "action": "created",
            "by": str(current_user.id),
            "at": datetime.utcnow().isoformat(),
            "status": attendance_in.status.value
        }]
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    
    return {
        "success": True,
        "message": "Attendance marked successfully",
        "data": record
    }


@router.post("/attendance/bulk", response_model=APIResponse)
def mark_bulk_attendance(
    request: BulkAttendanceRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.RoleChecker(["teacher", "admin"])),
):
    """Mark attendance for multiple students at once (Teacher only)"""
    
    # Prevent future dates
    if request.date.date() > datetime.now().date():
        return {
            "success": False,
            "message": "Cannot mark attendance for future dates",
            "data": None
        }

    # Verify teacher teaches this subject
    if not verify_teacher_teaches_subject(db, current_user.id, request.class_subject_id) and current_user.role != "admin":
        return {
            "success": False,
            "message": "You do not teach this subject",
            "data": None
        }

    # Get all existing attendance records for this date and subject
    existing_records = db.query(AttendanceRecord).filter(
        AttendanceRecord.class_subject_id == request.class_subject_id,
        func.date(AttendanceRecord.date) == request.date.date(),
    ).all()
    
    existing_student_ids = {r.student_id for r in existing_records}
    
    # Check if attendance already marked for entire class
    if existing_records:
        return {
            "success": False,
            "message": "Attendance for today is already marked.",
            "data": {"already_marked_count": len(existing_records)}
        }

    # Create attendance records
    created_records = []
    for record in request.records:
        attendance = AttendanceRecord(
            student_id=record.student_id,
            class_subject_id=request.class_subject_id,
            date=request.date,
            status=record.status,
            marked_by_id=current_user.id,
            audit_logs=[{
                "action": "created",
                "by": str(current_user.id),
                "at": datetime.utcnow().isoformat(),
                "status": record.status.value
            }]
        )
        db.add(attendance)
        created_records.append(attendance)

    db.commit()
    
    return {
        "success": True,
        "message": f"Attendance marked for {len(created_records)} students",
        "data": {"count": len(created_records)}
    }


@router.get("/attendance/my", response_model=APIResponse)
def get_my_attendance(
    class_subject_id: Optional[uuid.UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Get own attendance records (Students can only see their own)"""
    
    query = db.query(AttendanceRecord).filter(AttendanceRecord.student_id == current_user.id)
    
    if class_subject_id:
        query = query.filter(AttendanceRecord.class_subject_id == class_subject_id)
    
    if start_date:
        query = query.filter(func.date(AttendanceRecord.date) >= start_date.date())
    
    if end_date:
        query = query.filter(func.date(AttendanceRecord.date) <= end_date.date())
    
    records = query.order_by(AttendanceRecord.date.desc()).all()
    
    # Calculate attendance stats
    total = len(records)
    present = len([r for r in records if r.status == AttendanceStatus.present])
    absent = len([r for r in records if r.status == AttendanceStatus.absent])
    late = len([r for r in records if r.status == AttendanceStatus.late])
    excused = len([r for r in records if r.status == AttendanceStatus.excused])
    
    percentage = (present / total * 100) if total > 0 else 0
    
    stats = AttendanceStats(
        total_classes=total,
        present=present,
        absent=absent,
        late=late,
        excused=excused,
        percentage=round(percentage, 2)
    )
    
    return {
        "success": True,
        "message": "Attendance records retrieved successfully",
        "data": {
            "records": records,
            "stats": stats
        }
    }


@router.get("/attendance/student/{student_id}", response_model=APIResponse)
def get_student_attendance(
    student_id: uuid.UUID,
    class_subject_id: Optional[uuid.UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.RoleChecker(["teacher", "admin"])),
):
    """Get attendance records for a specific student (Teacher/Admin only)"""
    
    query = db.query(AttendanceRecord).filter(AttendanceRecord.student_id == student_id)
    
    if class_subject_id:
        query = query.filter(AttendanceRecord.class_subject_id == class_subject_id)
    
    if start_date:
        query = query.filter(func.date(AttendanceRecord.date) >= start_date.date())
    
    if end_date:
        query = query.filter(func.date(AttendanceRecord.date) <= end_date.date())
    
    records = query.order_by(AttendanceRecord.date.desc()).all()
    
    return {
        "success": True,
        "message": "Attendance records retrieved successfully",
        "data": records
    }


@router.get("/attendance/class/{class_subject_id}", response_model=APIResponse)
def get_class_attendance(
    class_subject_id: uuid.UUID,
    date: Optional[datetime] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.RoleChecker(["teacher", "admin"])),
):
    """Get attendance records for a class/subject on a specific date (Teacher/Admin only)"""
    
    query = db.query(AttendanceRecord).filter(AttendanceRecord.class_subject_id == class_subject_id)
    
    if date:
        query = query.filter(func.date(AttendanceRecord.date) == date.date())
    
    records = query.order_by(AttendanceRecord.student_id).all()
    
    return {
        "success": True,
        "message": "Attendance records retrieved successfully",
        "data": records
    }


@router.put("/attendance/{attendance_id}", response_model=APIResponse)
def update_attendance(
    attendance_id: uuid.UUID,
    update_data: AttendanceUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.RoleChecker(["teacher", "admin"])),
):
    """Edit attendance record with audit log (Teacher only)"""
    
    record = db.query(AttendanceRecord).filter(AttendanceRecord.id == attendance_id).first()
    
    if not record:
        return {
            "success": False,
            "message": "Attendance record not found",
            "data": None
        }
    
    # Get existing audit logs
    audit_logs = record.audit_logs or []
    
    # Add audit entry
    audit_logs.append({
        "action": "updated",
        "by": str(current_user.id),
        "at": datetime.utcnow().isoformat(),
        "old_status": record.status.value,
        "new_status": update_data.status.value if update_data.status else record.status.value,
        "reason": update_data.reason
    })
    
    # Update fields
    if update_data.status:
        record.status = update_data.status
    if update_data.reason:
        record.reason = update_data.reason
    
    record.audit_logs = audit_logs
    
    db.commit()
    db.refresh(record)
    
    return {
        "success": True,
        "message": "Attendance updated successfully",
        "data": record
    }


# ==================== ASSIGNMENT MODULE ====================

@router.post("/assignments", response_model=APIResponse)
def create_assignment(
    assignment_in: AssignmentCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.RoleChecker(["teacher", "admin"])),
):
    """Create a new assignment (Teacher only)"""
    
    # Get the actual class_subject_id
    class_subject_id = assignment_in.class_subject_id
    
    # If teacher_subject_id is provided instead of class_subject_id, look it up
    teacher_subject = db.query(TeacherSubject).filter(
        TeacherSubject.id == class_subject_id
    ).first()
    
    if teacher_subject:
        # teacher_subject_id was passed, use its class_subject_id
        actual_class_subject_id = teacher_subject.class_subject_id
    else:
        actual_class_subject_id = class_subject_id
    
    # Verify teacher teaches this subject
    if not verify_teacher_teaches_subject(db, current_user.id, actual_class_subject_id) and current_user.role != "admin":
        return {
            "success": False,
            "message": "You do not teach this subject",
            "data": None
        }

    assignment_data = assignment_in.model_dump()
    assignment_data["class_subject_id"] = actual_class_subject_id
    
    assignment = Assignment(**assignment_data)
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    
    return {
        "success": True,
        "message": "Assignment created successfully",
        "data": assignment
    }


@router.get("/assignments", response_model=APIResponse)
def list_assignments(
    class_subject_id: Optional[uuid.UUID] = None,
    teacher_subject_id: Optional[uuid.UUID] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """List assignments based on user role"""
    
    # If teacher_subject_id is provided, convert to class_subject_id
    if teacher_subject_id and not class_subject_id:
        teacher_subject = db.query(TeacherSubject).filter(
            TeacherSubject.id == teacher_subject_id
        ).first()
        if teacher_subject:
            class_subject_id = teacher_subject.class_subject_id
    
    query = db.query(Assignment)
    
    if current_user.role == "student":
        # Get student's enrolled subjects
        student_subjects = db.query(StudentSubject).filter(
            StudentSubject.student_id == current_user.id
        ).all()
        class_subject_ids = [s.class_subject_id for s in student_subjects]
        
        query = query.filter(Assignment.class_subject_id.in_(class_subject_ids))
        
    elif current_user.role in ["teacher", "admin"]:
        class_subject_ids = get_teacher_class_subject_ids(db, current_user.id) if current_user.role != "admin" else None
        
        if class_subject_ids:
            query = query.filter(Assignment.class_subject_id.in_(class_subject_ids))
    
    if class_subject_id:
        query = query.filter(Assignment.class_subject_id == class_subject_id)
    
    assignments = query.order_by(Assignment.created_at.desc()).all()
    
    # Add submission counts for teachers
    result = []
    for assignment in assignments:
        assignment_dict = {
            "id": assignment.id,
            "class_subject_id": assignment.class_subject_id,
            "title": assignment.title,
            "description": assignment.description,
            "due_date": assignment.due_date,
            "attachments": assignment.attachments,
            "allow_reupload": assignment.allow_reupload,
            "max_file_size_mb": assignment.max_file_size_mb,
            "allowed_file_types": assignment.allowed_file_types,
            "created_at": assignment.created_at,
            "updated_at": assignment.updated_at
        }
        
        if current_user.role in ["teacher", "admin"]:
            submission_count = db.query(AssignmentSubmission).filter(
                AssignmentSubmission.assignment_id == assignment.id
            ).count()
            graded_count = db.query(AssignmentSubmission).filter(
                AssignmentSubmission.assignment_id == assignment.id,
                AssignmentSubmission.is_graded == True
            ).count()
            assignment_dict["submission_count"] = submission_count
            assignment_dict["graded_count"] = graded_count
        
        result.append(assignment_dict)
    
    return {
        "success": True,
        "message": "Assignments retrieved successfully",
        "data": result
    }


@router.get("/assignments/{assignment_id}", response_model=APIResponse)
def get_assignment(
    assignment_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Get assignment details"""
    
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    
    if not assignment:
        return {
            "success": False,
            "message": "Assignment not found",
            "data": None
        }
    
    # Check access
    if current_user.role == "student":
        if not verify_student_enrolled(db, current_user.id, assignment.class_subject_id):
            return {
                "success": False,
                "message": "You are not enrolled in this subject",
                "data": None
            }
    
    return {
        "success": True,
        "message": "Assignment retrieved successfully",
        "data": assignment
    }


@router.put("/assignments/{assignment_id}", response_model=APIResponse)
def update_assignment(
    assignment_id: uuid.UUID,
    update_data: AssignmentUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.RoleChecker(["teacher", "admin"])),
):
    """Update assignment details (Teacher only)"""
    
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    
    if not assignment:
        return {
            "success": False,
            "message": "Assignment not found",
            "data": None
        }
    
    # Verify teacher owns this assignment
    if not verify_teacher_teaches_subject(db, current_user.id, assignment.class_subject_id) and current_user.role != "admin":
        return {
            "success": False,
            "message": "You cannot edit this assignment",
            "data": None
        }
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(assignment, key, value)
    
    assignment.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(assignment)
    
    return {
        "success": True,
        "message": "Assignment updated successfully",
        "data": assignment
    }


@router.delete("/assignments/{assignment_id}", response_model=APIResponse)
def delete_assignment(
    assignment_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.RoleChecker(["teacher", "admin"])),
):
    """Delete an assignment (Teacher only)"""
    
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    
    if not assignment:
        return {
            "success": False,
            "message": "Assignment not found",
            "data": None
        }
    
    # Verify teacher owns this assignment
    if not verify_teacher_teaches_subject(db, current_user.id, assignment.class_subject_id) and current_user.role != "admin":
        return {
            "success": False,
            "message": "You cannot delete this assignment",
            "data": None
        }
    
    db.delete(assignment)
    db.commit()
    
    return {
        "success": True,
        "message": "Assignment deleted successfully",
        "data": None
    }


@router.post("/assignments/{assignment_id}/submit", response_model=APIResponse)
def submit_assignment(
    assignment_id: uuid.UUID,
    submission_in: AssignmentSubmissionCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.RoleChecker(["student", "admin"])),
):
    """Submit an assignment (Student only)"""
    
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    
    if not assignment:
        return {
            "success": False,
            "message": "Assignment not found",
            "data": None
        }
    
    # Verify student is enrolled
    if not verify_student_enrolled(db, current_user.id, assignment.class_subject_id):
        return {
            "success": False,
            "message": "You are not enrolled in this subject",
            "data": None
        }
    
    # Check deadline
    if assignment.due_date and datetime.now(assignment.due_date.tzinfo) > assignment.due_date:
        return {
            "success": False,
            "message": "Submission deadline has passed",
            "data": None
        }
    
    # Check if submission already exists
    existing_submission = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.assignment_id == assignment_id,
        AssignmentSubmission.student_id == current_user.id
    ).first()
    
    if existing_submission:
        if not assignment.allow_reupload:
            return {
                "success": False,
                "message": "Re-upload is not allowed for this assignment",
                "data": None
            }
        
        # Update existing submission
        existing_submission.file_url = submission_in.file_url
        existing_submission.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing_submission)
        
        return {
            "success": True,
            "message": "Submission updated successfully",
            "data": existing_submission
        }
    
    # Create new submission
    submission = AssignmentSubmission(
        assignment_id=assignment_id,
        student_id=current_user.id,
        file_url=submission_in.file_url
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    
    return {
        "success": True,
        "message": "Assignment submitted successfully",
        "data": submission
    }


@router.delete("/assignments/{assignment_id}/submit", response_model=APIResponse)
def delete_submission(
    assignment_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.RoleChecker(["student", "admin"])),
):
    """Delete own submission before deadline (Student only)"""
    
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    
    if not assignment:
        return {
            "success": False,
            "message": "Assignment not found",
            "data": None
        }
    
    # Check if deadline has passed
    if assignment.due_date and datetime.now(assignment.due_date.tzinfo) > assignment.due_date:
        return {
            "success": False,
            "message": "Cannot delete submission after deadline",
            "data": None
        }
    
    submission = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.assignment_id == assignment_id,
        AssignmentSubmission.student_id == current_user.id
    ).first()
    
    if not submission:
        return {
            "success": False,
            "message": "No submission found",
            "data": None
        }
    
    db.delete(submission)
    db.commit()
    
    return {
        "success": True,
        "message": "Submission deleted successfully",
        "data": None
    }


@router.get("/assignments/{assignment_id}/submissions", response_model=APIResponse)
def view_submissions(
    assignment_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """View submissions for an assignment"""
    
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    
    if not assignment:
        return {
            "success": False,
            "message": "Assignment not found",
            "data": None
        }
    
    if current_user.role == "student":
        # Students can only see their own submissions
        submissions = db.query(AssignmentSubmission).filter(
            AssignmentSubmission.assignment_id == assignment_id,
            AssignmentSubmission.student_id == current_user.id
        ).all()
        
        # Include grade and feedback for student's own submission
        return {
            "success": True,
            "message": "Submissions retrieved successfully",
            "data": submissions
        }
    
    # Teachers can see all submissions
    if not verify_teacher_teaches_subject(db, current_user.id, assignment.class_subject_id) and current_user.role != "admin":
        return {
            "success": False,
            "message": "You do not teach this subject",
            "data": None
        }
    
    submissions = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.assignment_id == assignment_id
    ).all()
    
    return {
        "success": True,
        "message": "Submissions retrieved successfully",
        "data": submissions
    }


@router.put("/assignments/{assignment_id}/submissions/{submission_id}/grade", response_model=APIResponse)
def grade_submission(
    assignment_id: uuid.UUID,
    submission_id: uuid.UUID,
    grade_data: GradeSubmissionRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.RoleChecker(["teacher", "admin"])),
):
    """Grade a submission (Teacher only)"""
    
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    
    if not assignment:
        return {
            "success": False,
            "message": "Assignment not found",
            "data": None
        }
    
    # Verify teacher teaches this subject
    if not verify_teacher_teaches_subject(db, current_user.id, assignment.class_subject_id) and current_user.role != "admin":
        return {
            "success": False,
            "message": "You do not teach this subject",
            "data": None
        }
    
    submission = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.id == submission_id,
        AssignmentSubmission.assignment_id == assignment_id
    ).first()
    
    if not submission:
        return {
            "success": False,
            "message": "Submission not found",
            "data": None
        }
    
    submission.grade = grade_data.grade
    submission.feedback = grade_data.feedback
    submission.is_graded = True
    submission.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(submission)
    
    return {
        "success": True,
        "message": "Submission graded successfully",
        "data": submission
    }


@router.put("/assignments/{assignment_id}/submissions/{submission_id}", response_model=APIResponse)
def update_grade(
    assignment_id: uuid.UUID,
    submission_id: uuid.UUID,
    grade_data: GradeSubmissionRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.RoleChecker(["teacher", "admin"])),
):
    """Update grade and feedback (Teacher only)"""
    return grade_submission(assignment_id, submission_id, grade_data, db, current_user)


# ==================== LECTURE MODULE ====================

@router.post("/lectures", response_model=APIResponse)
def create_lecture(
    lecture_in: LectureCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.RoleChecker(["teacher", "admin"])),
):
    """Create a new lecture (Teacher only)"""
    
    # Verify teacher teaches this subject
    if not verify_teacher_teaches_subject(db, current_user.id, lecture_in.class_subject_id) and current_user.role != "admin":
        return {
            "success": False,
            "message": "You do not teach this subject",
            "data": None
        }

    lecture = Lecture(**lecture_in.model_dump(), author_id=current_user.id)
    db.add(lecture)
    db.commit()
    db.refresh(lecture)
    
    return {
        "success": True,
        "message": "Lecture created successfully",
        "data": lecture
    }


@router.get("/lectures", response_model=APIResponse)
def list_lectures(
    class_subject_id: Optional[uuid.UUID] = None,
    published_only: bool = True,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """List lectures based on user role"""
    
    query = db.query(Lecture)
    
    if current_user.role == "student":
        # Get student's enrolled subjects
        student_subjects = db.query(StudentSubject).filter(
            StudentSubject.student_id == current_user.id
        ).all()
        class_subject_ids = [s.class_subject_id for s in student_subjects]
        
        query = query.filter(Lecture.class_subject_id.in_(class_subject_ids))
        
        if published_only:
            query = query.filter(Lecture.is_published == True)
        
    elif current_user.role in ["teacher", "admin"]:
        class_subject_ids = get_teacher_class_subject_ids(db, current_user.id) if current_user.role != "admin" else None
        
        if class_subject_ids:
            query = query.filter(Lecture.class_subject_id.in_(class_subject_ids))
    
    if class_subject_id:
        query = query.filter(Lecture.class_subject_id == class_subject_id)
    
    lectures = query.order_by(Lecture.scheduled_at.desc(), Lecture.created_at.desc()).all()
    
    return {
        "success": True,
        "message": "Lectures retrieved successfully",
        "data": lectures
    }


@router.get("/lectures/{lecture_id}", response_model=APIResponse)
def get_lecture(
    lecture_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Get lecture details and increment view count"""
    
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
    
    if not lecture:
        return {
            "success": False,
            "message": "Lecture not found",
            "data": None
        }
    
    # Check access for students
    if current_user.role == "student":
        if not verify_student_enrolled(db, current_user.id, lecture.class_subject_id):
            return {
                "success": False,
                "message": "You are not enrolled in this subject",
                "data": None
            }
        
        if not lecture.is_published:
            return {
                "success": False,
                "message": "This lecture is not yet published",
                "data": None
            }
    
    # Increment view count
    lecture.view_count += 1
    db.commit()
    db.refresh(lecture)
    
    return {
        "success": True,
        "message": "Lecture retrieved successfully",
        "data": lecture
    }


@router.put("/lectures/{lecture_id}", response_model=APIResponse)
def update_lecture(
    lecture_id: uuid.UUID,
    update_data: LectureUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.RoleChecker(["teacher", "admin"])),
):
    """Update lecture details (Teacher only)"""
    
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
    
    if not lecture:
        return {
            "success": False,
            "message": "Lecture not found",
            "data": None
        }
    
    # Verify teacher owns this lecture
    if lecture.author_id != current_user.id and current_user.role != "admin":
        return {
            "success": False,
            "message": "You cannot edit this lecture",
            "data": None
        }
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(lecture, key, value)
    
    db.commit()
    db.refresh(lecture)
    
    return {
        "success": True,
        "message": "Lecture updated successfully",
        "data": lecture
    }


@router.delete("/lectures/{lecture_id}", response_model=APIResponse)
def delete_lecture(
    lecture_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.RoleChecker(["teacher", "admin"])),
):
    """Delete a lecture (Teacher only)"""
    
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
    
    if not lecture:
        return {
            "success": False,
            "message": "Lecture not found",
            "data": None
        }
    
    # Verify teacher owns this lecture
    if lecture.author_id != current_user.id and current_user.role != "admin":
        return {
            "success": False,
            "message": "You cannot delete this lecture",
            "data": None
        }
    
    db.delete(lecture)
    db.commit()
    
    return {
        "success": True,
        "message": "Lecture deleted successfully",
        "data": None
    }


@router.put("/lectures/{lecture_id}/visibility", response_model=APIResponse)
def toggle_lecture_visibility(
    lecture_id: uuid.UUID,
    is_published: bool,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.RoleChecker(["teacher", "admin"])),
):
    """Toggle lecture visibility (draft/published) (Teacher only)"""
    
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
    
    if not lecture:
        return {
            "success": False,
            "message": "Lecture not found",
            "data": None
        }
    
    # Verify teacher owns this lecture
    if lecture.author_id != current_user.id and current_user.role != "admin":
        return {
            "success": False,
            "message": "You cannot modify this lecture",
            "data": None
        }
    
    lecture.is_published = is_published
    db.commit()
    db.refresh(lecture)
    
    status = "published" if is_published else "draft"
    return {
        "success": True,
        "message": f"Lecture {status} successfully",
        "data": lecture
    }


@router.get("/lectures/{lecture_id}/download", response_model=APIResponse)
def download_lecture_content(
    lecture_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Download lecture content and increment download count"""
    
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
    
    if not lecture:
        return {
            "success": False,
            "message": "Lecture not found",
            "data": None
        }
    
    # Check access
    if current_user.role == "student":
        if not verify_student_enrolled(db, current_user.id, lecture.class_subject_id):
            return {
            "success": False,
            "message": "You are not enrolled in this subject",
            "data": None
        }
        
        if not lecture.is_published:
            return {
                "success": False,
                "message": "This lecture is not yet published",
                "data": None
            }
    
    # Increment download count
    lecture.download_count += 1
    db.commit()
    
    return {
        "success": True,
        "message": "Download started",
        "data": {
            "content_url": lecture.content_url,
            "download_count": lecture.download_count
        }
    }


# ==================== FILE UPLOAD ENDPOINT ====================

@router.post("/upload", response_model=APIResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(deps.get_current_user),
):
    """Upload a file securely"""
    
    # Validate file types
    allowed_types = [
        "application/pdf",
        "video/mp4", "video/webm", "video/quicktime",
        "image/jpeg", "image/png", "image/gif",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "application/zip"
    ]
    
    # Max file size (10MB default)
    max_size = 10 * 1024 * 1024
    
    # Validate content type
    if file.content_type not in allowed_types:
        return {
            "success": False,
            "message": f"File type {file.content_type} is not allowed",
            "data": None
        }
    
    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ""
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    
    # Create upload directory if not exists
    upload_dir = os.path.join(settings.UPLOAD_DIR, "lms")
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Save file
    content = await file.read()
    
    # Validate file size
    if len(content) > max_size:
        return {
            "success": False,
            "message": f"File size exceeds maximum allowed ({max_size // (1024*1024)}MB)",
            "data": None
        }
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    file_url = f"/uploads/lms/{unique_filename}"
    
    return {
        "success": True,
        "message": "File uploaded successfully",
        "data": {
            "file_url": file_url,
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(content)
        }
    }


# ==================== CLASS/SUBJECT ENDPOINTS ====================

@router.get("/classes", response_model=APIResponse)
def get_classes(db: Session = Depends(deps.get_db)):
    """Get all classes"""
    classes = db.query(Class).all()
    return {
        "success": True,
        "message": "Classes retrieved successfully",
        "data": classes
    }


@router.get("/classes/{class_id}/sections", response_model=APIResponse)
def get_sections(class_id: uuid.UUID, db: Session = Depends(deps.get_db)):
    """Get sections for a class"""
    sections = db.query(Section).filter(Section.class_id == class_id).all()
    return {
        "success": True,
        "message": "Sections retrieved successfully",
        "data": sections
    }


@router.get("/subjects", response_model=APIResponse)
def get_subjects(db: Session = Depends(deps.get_db)):
    """Get all subjects"""
    subjects = db.query(Subject).all()
    return {
        "success": True,
        "message": "Subjects retrieved successfully",
        "data": subjects
    }


@router.get("/classes/{class_id}/subjects", response_model=APIResponse)
def get_class_subjects(class_id: uuid.UUID, db: Session = Depends(deps.get_db)):
    """Get subjects for a class"""
    class_subjects = db.query(ClassSubject).filter(ClassSubject.class_id == class_id).all()
    return {
        "success": True,
        "message": "Class subjects retrieved successfully",
        "data": class_subjects
    }


@router.get("/my/subjects", response_model=APIResponse)
def get_my_subjects(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Get current user's enrolled/subject teaching subjects"""
    
    if current_user.role == "student":
        student_subjects = db.query(StudentSubject).filter(
            StudentSubject.student_id == current_user.id
        ).all()
        
        result = []
        for ss in student_subjects:
            result.append({
                "id": ss.class_subject_id,
                "subject_name": ss.subject.name if ss.subject else None,
                "subject_code": ss.subject.code if ss.subject else None,
                "class_name": ss.class_.name if ss.class_ else None
            })
        
        return {
            "success": True,
            "message": "Subjects retrieved successfully",
            "data": result
        }
    
    elif current_user.role in ["teacher", "admin"]:
        teacher_subjects = db.query(TeacherSubject).filter(
            TeacherSubject.teacher_id == current_user.id
        ).all()
        
        result = []
        for ts in teacher_subjects:
            result.append({
                "id": ts.class_subject_id,
                "subject_name": ts.subject.name if ts.subject else None,
                "subject_code": ts.subject.code if ts.subject else None,
                "class_name": ts.class_.name if ts.class_ else None,
                "section_name": ts.section.name if ts.section else None
            })
        
        return {
            "success": True,
            "message": "Subjects retrieved successfully",
            "data": result
        }
    
    return {
        "success": False,
        "message": "Invalid role",
        "data": None
    }
