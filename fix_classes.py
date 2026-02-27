from app.core.database import SessionLocal
from app.models.lms import Class, AcademicYear

db = SessionLocal()
target_year_id = "40544b44-c6e1-4890-ac44-cef26053c1e7"

try:
    year = db.query(AcademicYear).filter(AcademicYear.id == target_year_id).first()
    if not year:
        # Fallback to current year if target not found
        year = db.query(AcademicYear).filter(AcademicYear.is_current == True).first()
    
    if not year:
        print("No academic year found to link classes to.")
    else:
        print(f"Linking classes to Academic Year: {year.name} ({year.id})")
        classes = db.query(Class).filter(Class.academic_year_id == None).all()
        for c in classes:
            c.academic_year_id = year.id
            print(f"  Linked Class: {c.name}")
        
        db.commit()
        print(f"Successfully linked {len(classes)} classes.")

finally:
    db.close()
