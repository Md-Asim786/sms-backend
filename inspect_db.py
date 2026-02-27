from app.core.database import SessionLocal
from app.models.lms import Class, ClassSubject, Subject

db = SessionLocal()
try:
    classes = db.query(Class).all()
    print(f"Total Classes: {len(classes)}")
    for c in classes:
        subjects = db.query(ClassSubject).filter(ClassSubject.class_id == c.id).all()
        print(f"  Class: {c.name} ({c.id}) - Year ID: {c.academic_year_id}")
        if not subjects:
            print("    [!] No subjects assigned")
        for cs in subjects:
            subj = db.query(Subject).filter(Subject.id == cs.subject_id).first()
            print(f"    - {subj.name if subj else 'Unknown'} | Periods: {cs.periods_per_week}")

finally:
    db.close()
