from fastapi.testclient import TestClient
from app.main import app
from app.core import security
from app.models.auth import User
from app.models.users import EnrolledStudent, EnrolledEmployee, UserRole
from app.models.lms import Class, Section, Subject, ClassSubject, TeacherSubject
from app.core.database import SessionLocal
import uuid
import json

client = TestClient(app)

def verify_lms_data_fetching():
    db = SessionLocal()
    
    # Setup test data
    test_id = uuid.uuid4().hex[:6]
    teacher_email = f"teacher-{test_id}@example.com"
    student_email = f"student-{test_id}@example.com"
    password = "testpassword123"
    
    try:
        # 1. Setup Class and Subject
        cls = Class(id=uuid.uuid4(), name=f"Test Class {test_id}")
        sec = Section(id=uuid.uuid4(), name="A", class_id=cls.id)
        sub = Subject(id=uuid.uuid4(), name=f"Test Subject {test_id}", code=f"TS-{test_id}")
        db.add_all([cls, sec, sub])
        db.commit()
        
        cs = ClassSubject(id=uuid.uuid4(), class_id=cls.id, subject_id=sub.id)
        db.add(cs)
        db.commit()

        # 2. Setup Teacher
        t_user = User(
            email=teacher_email,
            password_hash=security.get_password_hash(password),
            role=UserRole.teacher,
            is_active=True
        )
        db.add(t_user)
        db.commit()
        
        teacher = EnrolledEmployee(
            id=uuid.uuid4(),
            user_id=t_user.id,
            employee_id=f"T-{test_id}",
            first_name="Test",
            last_name="Teacher",
            email=teacher_email,
            phone="1234567890",
            gender="Male",
            date_of_birth="1980-01-01",
            employee_type="teaching",
            functional_role="Teacher",
            system_role="teacher",
            highest_qualification="PhD",
            experience_years="10"
        )
        db.add(teacher)
        db.commit()
        
        ts = TeacherSubject(
            id=uuid.uuid4(),
            teacher_id=teacher.id,
            class_id=cls.id,
            section_id=sec.id,
            subject_id=sub.id,
            class_subject_id=cs.id
        )
        db.add(ts)
        db.commit()

        # 3. Setup Student
        s_user = User(
            email=student_email,
            password_hash=security.get_password_hash(password),
            role=UserRole.student,
            is_active=True
        )
        db.add(s_user)
        db.commit()
        
        student = EnrolledStudent(
            id=uuid.uuid4(),
            user_id=s_user.id,
            system_student_id=f"S-{test_id}",
            admission_number=f"ADM-{test_id}",
            first_name="Test",
            last_name="Student",
            gender="Female",
            date_of_birth="2010-01-01",
            b_form_number="1234567890",
            guardian_name="Guardian",
            guardian_cnic="12345-6789012-3",
            guardian_phone="0987654321",
            guardian_email="guardian@example.com",
            class_id=cls.id,
            section_id=sec.id,
            lms_email=student_email,
            lms_login=student_email,
            lms_password=password
        )
        db.add(student)
        db.commit()

        # 4. Test API Endpoints
        for email, role in [(teacher_email, "teacher"), (student_email, "student")]:
            print(f"\n--- Verifying {role.capitalize()} Endpoints ({email}) ---")
            
            # Login
            login_res = client.post("/api/v1/auth/login", data={"username": email, "password": password})
            assert login_res.status_code == 200
            token = login_res.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Profile
            profile_res = client.get("/api/v1/user-profile/me", headers=headers)
            print(f"Profile Status: {profile_res.status_code}")
            assert profile_res.status_code == 200
            profile_data = profile_res.json()
            print(f"Profile Data: {json.dumps(profile_data, indent=2)}")
            assert profile_data["role"] == role
            
            # Academic Info
            acad_res = client.get("/api/v1/user-profile/academic-info", headers=headers)
            print(f"Academic Info Status: {acad_res.status_code}")
            assert acad_res.status_code == 200
            acad_data = acad_res.json()
            print(f"Academic Info Data: {json.dumps(acad_data, indent=2)}")
            assert len(acad_data["subjects"]) > 0

        print("\nAll verifications passed!")

    except Exception as e:
        print(f"Verification Failed: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        # Cleanup (Note: in a real test you'd want to be more careful, but this is for validation)
        # We delete in reverse order of dependencies
        try:
            db.query(TeacherSubject).filter(TeacherSubject.teacher_id == teacher.id).delete()
            db.query(EnrolledStudent).filter(EnrolledStudent.user_id == s_user.id).delete()
            db.query(EnrolledEmployee).filter(EnrolledEmployee.user_id == t_user.id).delete()
            db.query(User).filter(User.id.in_([t_user.id, s_user.id])).delete()
            db.query(ClassSubject).filter(ClassSubject.id == cs.id).delete()
            db.query(Section).filter(Section.id == sec.id).delete()
            db.query(Subject).filter(Subject.id == sub.id).delete()
            db.query(Class).filter(Class.id == cls.id).delete()
            db.commit()
            print("Cleanup complete.")
        except:
             db.rollback()
        db.close()

if __name__ == "__main__":
    verify_lms_data_fetching()
