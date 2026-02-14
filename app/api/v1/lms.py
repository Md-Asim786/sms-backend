from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

from app.api import deps
from app.models.lms import Class, Section, Subject, ClassSubject, AttendanceRecord
from app.schemas.lms import (
    ClassResponse,
    SectionResponse,
    SubjectResponse,
    ClassSubjectResponse,
    AttendanceCreate,
    AttendanceResponse,
)

router = APIRouter()


# Classes
@router.get("/classes", response_model=List[ClassResponse])
def get_classes(db: Session = Depends(deps.get_db)):
    return db.query(Class).all()


# Sections
@router.get("/sections", response_model=List[SectionResponse])
def get_all_sections(db: Session = Depends(deps.get_db)):
    return db.query(Section).all()


@router.get("/classes/{class_id}/sections", response_model=List[SectionResponse])
def get_sections(class_id: uuid.UUID, db: Session = Depends(deps.get_db)):
    return db.query(Section).filter(Section.class_id == class_id).all()


# Subjects
@router.get("/subjects", response_model=List[SubjectResponse])
def get_subjects(db: Session = Depends(deps.get_db)):
    return db.query(Subject).all()


# Class Subjects (Mapping)
@router.get("/classes/{class_id}/subjects", response_model=List[ClassSubjectResponse])
def get_class_subjects(class_id: uuid.UUID, db: Session = Depends(deps.get_db)):
    return db.query(ClassSubject).filter(ClassSubject.class_id == class_id).all()


# Attendance
@router.post("/attendance", response_model=AttendanceResponse)
def mark_attendance(
    attendance_in: AttendanceCreate,
    db: Session = Depends(deps.get_db),
    # Teacher or Admin
    current_user: Any = Depends(deps.get_current_user),
):
    # TODO: Check if user is teacher of this class or admin
    record = AttendanceRecord(**attendance_in.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
