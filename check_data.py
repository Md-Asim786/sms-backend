from sqlalchemy import create_url
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.lms import Class, ClassSubject, TeacherSubject
from app.models.timetable import TimetableConfig

db = SessionLocal()
try:
    classes = db.query(Class).all()
    print(f"Total classes: {len(classes)}")
    for cls in classes:
        subjects = db.query(ClassSubject).filter(ClassSubject.class_id == cls.id).all()
        print(f"  Class {cls.name} (ID: {cls.id}): {len(subjects)} subjects")
        for cs in subjects:
            ts = db.query(TeacherSubject).filter(TeacherSubject.class_subject_id == cs.id).all()
            print(f"    Subject {cs.id}: {len(ts)} teacher assignments, {cs.periods_per_week} periods/week")
            
    configs = db.query(TimetableConfig).all()
    print(f"Total configs: {len(configs)}")
    for cfg in configs:
        print(f"  Config for year {cfg.academic_year_id}: {cfg.working_days}, {cfg.periods_per_day} p/day")
finally:
    db.close()
