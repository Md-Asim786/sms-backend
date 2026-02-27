from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.schemas import timetable as schemas
from app.models import timetable as models
from app.services.scheduling_engine import SchedulingEngine

router = APIRouter()

# --- Configuration Endpoints ---

@router.post("/config", response_model=schemas.TimetableConfig)
def set_config(config: schemas.TimetableConfigCreate, db: Session = Depends(get_db)):
    # Check if config already exists for this academic year
    db_config = db.query(models.TimetableConfig).filter(
        models.TimetableConfig.academic_year_id == config.academic_year_id
    ).first()
    
    if db_config:
        # Update existing
        for key, value in config.model_dump().items():
            setattr(db_config, key, value)
    else:
        # Create new
        db_config = models.TimetableConfig(**config.model_dump())
        db.add(db_config)
    
    db.commit()
    db.refresh(db_config)
    return db_config

@router.patch("/config/{config_id}", response_model=schemas.TimetableConfig)
def update_config(config_id: UUID, config_update: schemas.TimetableConfigUpdate, db: Session = Depends(get_db)):
    db_config = db.query(models.TimetableConfig).filter(models.TimetableConfig.id == config_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    update_data = config_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_config, key, value)
    
    db.commit()
    db.refresh(db_config)
    return db_config

@router.get("/config/{academic_year_id}", response_model=schemas.TimetableConfig)
def get_config(academic_year_id: UUID, db: Session = Depends(get_db)):
    config = db.query(models.TimetableConfig).filter(
        models.TimetableConfig.academic_year_id == academic_year_id
    ).order_by(models.TimetableConfig.created_at.desc()).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    return config

@router.get("/versions/{academic_year_id}", response_model=List[schemas.TimetableVersion])
def get_versions(academic_year_id: UUID, db: Session = Depends(get_db)):
    return db.query(models.TimetableVersion).filter(
        models.TimetableVersion.academic_year_id == academic_year_id
    ).order_by(models.TimetableVersion.created_at.desc()).all()

@router.patch("/versions/{version_id}/activate", response_model=schemas.TimetableVersion)
def activate_version(version_id: UUID, db: Session = Depends(get_db)):
    version = db.query(models.TimetableVersion).filter(models.TimetableVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    # Deactivate all others for this academic year
    db.query(models.TimetableVersion).filter(
        models.TimetableVersion.academic_year_id == version.academic_year_id
    ).update({"is_active": False})
    
    version.is_active = True
    db.commit()
    db.refresh(version)
    return version

# --- Constraint Endpoints ---

@router.post("/constraints/teacher", response_model=schemas.TeacherConstraint)
def set_teacher_constraint(constraint: schemas.TeacherConstraintCreate, db: Session = Depends(get_db)):
    # Update if exists, else create
    db_constraint = db.query(models.TeacherConstraint).filter(
        models.TeacherConstraint.teacher_id == constraint.teacher_id,
        models.TeacherConstraint.academic_year_id == constraint.academic_year_id
    ).first()
    
    if db_constraint:
        for key, value in constraint.model_dump().items():
            setattr(db_constraint, key, value)
    else:
        db_constraint = models.TeacherConstraint(**constraint.model_dump())
        db.add(db_constraint)
    
    db.commit()
    db.refresh(db_constraint)
    return db_constraint

@router.post("/constraints/subject", response_model=schemas.SubjectConstraint)
def set_subject_constraint(constraint: schemas.SubjectConstraintCreate, db: Session = Depends(get_db)):
    db_constraint = db.query(models.SubjectConstraint).filter(
        models.SubjectConstraint.class_subject_id == constraint.class_subject_id
    ).first()
    
    if db_constraint:
        for key, value in constraint.model_dump().items():
            setattr(db_constraint, key, value)
    else:
        db_constraint = models.SubjectConstraint(**constraint.model_dump())
        db.add(db_constraint)
    
    db.commit()
    db.refresh(db_constraint)
    return db_constraint

# --- Generation Endpoints ---

@router.post("/generate", response_model=schemas.TimetableVersion)
def generate_timetable(request: schemas.TimetableGenerationRequest, db: Session = Depends(get_db)):
    try:
        engine = SchedulingEngine(db, request.academic_year_id)
        version = engine.generate(request.version_name, request.class_ids)
        if not version:
            raise HTTPException(status_code=400, detail="Could not generate any slots. Please check if subjects and teachers are correctly assigned.")
        return version
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

# --- Retrieval Endpoints ---

@router.get("/class/{class_id}", response_model=List[schemas.TimetableSlot])
def get_class_timetable(class_id: UUID, section_id: Optional[UUID] = None, version_id: Optional[UUID] = None, db: Session = Depends(get_db)):
    query = db.query(models.TimetableSlot).filter(models.TimetableSlot.class_id == class_id)
    if section_id:
        query = query.filter(models.TimetableSlot.section_id == section_id)
    if version_id:
        query = query.filter(models.TimetableSlot.version_id == version_id)
    else:
        # Get from active version
        active_version = db.query(models.TimetableVersion).filter(
            models.TimetableVersion.is_active == True
        ).first()
        if active_version:
            query = query.filter(models.TimetableSlot.version_id == active_version.id)
        else:
            return []
            
    return query.order_by(models.TimetableSlot.day, models.TimetableSlot.period_index).all()

@router.get("/class/{class_id}/subjects")
def get_class_subjects(class_id: UUID, db: Session = Depends(get_db)):
    from app.models.lms import ClassSubject
    return db.query(ClassSubject).filter(ClassSubject.class_id == class_id).all()

@router.get("/teacher/{teacher_id}", response_model=List[schemas.TimetableSlot])
def get_teacher_schedule(teacher_id: UUID, version_id: Optional[UUID] = None, db: Session = Depends(get_db)):
    query = db.query(models.TimetableSlot).filter(models.TimetableSlot.teacher_id == teacher_id)
    if version_id:
        query = query.filter(models.TimetableSlot.version_id == version_id)
    else:
        # Get from active version
        active_version = db.query(models.TimetableVersion).filter(
            models.TimetableVersion.is_active == True
        ).first()
        if active_version:
            query = query.filter(models.TimetableSlot.version_id == active_version.id)
        else:
            return []
            
    return query.order_by(models.TimetableSlot.day, models.TimetableSlot.period_index).all()

@router.get("/teacher/{teacher_id}/constraint", response_model=Optional[schemas.TeacherConstraint])
def get_teacher_constraint(teacher_id: UUID, academic_year_id: UUID, db: Session = Depends(get_db)):
    return db.query(models.TeacherConstraint).filter(
        models.TeacherConstraint.teacher_id == teacher_id,
        models.TeacherConstraint.academic_year_id == academic_year_id
    ).first()

@router.get("/teacher/{teacher_id}/subjects")
def get_teacher_subjects(teacher_id: UUID, db: Session = Depends(get_db)):
    # Assuming TeacherSubject model exists as seen in admin.py imports earlier
    from app.models.lms import TeacherSubject
    return db.query(TeacherSubject).filter(TeacherSubject.teacher_id == teacher_id).all()

@router.get("/rooms", response_model=List[schemas.Room])
def get_rooms(db: Session = Depends(get_db)):
    return db.query(models.Room).filter(models.Room.is_active == True).all()

@router.post("/rooms", response_model=schemas.Room)
def create_room(room: schemas.RoomCreate, db: Session = Depends(get_db)):
    db_room = models.Room(**room.model_dump())
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

@router.delete("/rooms/{room_id}")
def delete_room(room_id: UUID, db: Session = Depends(get_db)):
    db_room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not db_room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    db.delete(db_room)
    db.commit()
    return {"message": "Room deleted successfully"}

@router.post("/slots", response_model=schemas.TimetableSlot)
def create_slot(slot: schemas.TimetableSlotCreate, db: Session = Depends(get_db)):
    db_slot = models.TimetableSlot(**slot.model_dump())
    db.add(db_slot)
    db.commit()
    db.refresh(db_slot)
    return db_slot

@router.delete("/versions/{version_id}")
def delete_version(version_id: UUID, db: Session = Depends(get_db)):
    version = db.query(models.TimetableVersion).filter(models.TimetableVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    if version.is_active:
        raise HTTPException(status_code=400, detail="Cannot delete the active version. Deactivate it first by activating another version.")
    if version.is_locked:
        raise HTTPException(status_code=400, detail="Cannot delete a locked version.")
    db.delete(version)
    db.commit()
    return {"message": "Version deleted successfully"}
