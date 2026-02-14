from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

from app.api import deps
from app.core.database import get_db
from app.models.users import EnrolledStudent
from app.schemas.users import EnrolledStudentResponse, EnrolledStudentUpdate




from app.models.lms import ClassSubject
from app.models.finance import FeePayment
from app.models.exams import Result
from app.schemas import FeePaymentResponse

router = APIRouter()

# This depends on the user being logged in and having their student ID associated.
# We'll use a dependency to get the current user and their student profile.


@router.get("/dashboard")
def get_student_dashboard(
    current_user: Any = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
):
    student = (
        db.query(EnrolledStudent)
        .filter(EnrolledStudent.user_id == current_user.id)
        .first()
    )
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    # Mocked data - replace with real queries
    total_pending = 15000
    paid_this_year = 60000

    return {
        "currentClass": student.class_.name,
        "grade": "A+",  # This would be calculated
        "totalPending": f"Rs {total_pending}",
        "totalPaid": f"Rs {paid_this_year}",
    }


@router.get("/academic-info")
def get_academic_info(
    current_user: Any = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
):
    student = (
        db.query(EnrolledStudent)
        .filter(EnrolledStudent.user_id == current_user.id)
        .first()
    )
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    subjects = (
        db.query(ClassSubject).filter(ClassSubject.class_id == student.class_id).all()
    )

    return {
        "currentClass": student.class_.name,
        "section": student.section.name,
        "subjects": [
            {
                "name": cs.subject.name,
                "teacher": f"{cs.teacher.first_name} {cs.teacher.last_name}"
                if cs.teacher
                else "N/A",
            }
            for cs in subjects
        ],
    }


@router.get("/fee-history", response_model=List[FeePaymentResponse])
def get_fee_history(
    current_user: Any = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
):
    student = (
        db.query(EnrolledStudent)
        .filter(EnrolledStudent.user_id == current_user.id)
        .first()
    )
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    return db.query(FeePayment).filter(FeePayment.student_id == student.id).all()


@router.get(
    "/results", response_model=List[Any]
)  # Create a proper Result schema if needed
def get_results(
    current_user: Any = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
):
    student = (
        db.query(EnrolledStudent)
        .filter(EnrolledStudent.user_id == current_user.id)
        .first()
    )
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    return db.query(Result).filter(Result.student_id == student.id).all()


@router.get("/personal-info", response_model=EnrolledStudentResponse)
def get_personal_info(
    current_user: Any = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
):
    student = (
        db.query(EnrolledStudent)
        .filter(EnrolledStudent.user_id == current_user.id)
        .first()
    )
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return student
