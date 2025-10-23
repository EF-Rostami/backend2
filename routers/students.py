from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from database import get_db
from dependencies import get_current_user, require_roles
from models import User, Role, RoleUser, Student, Grade, Course, Attendance, FeeRecord
from schemas.student import StudentCreate, StudentResponse
from utils.security import get_password_hash
from utils.enums import RoleType

router = APIRouter(prefix="/students", tags=["students"])

@router.post("", response_model=StudentResponse)
async def create_student(
    student: StudentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    hashed_password = get_password_hash(student.password)
    new_user = User(
        email=student.email,
        firstName=student.firstName,
        lastName=student.lastName,
        password_hash=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    role = db.query(Role).filter(Role.name == RoleType.STUDENT).first()
    if not role:
        role = Role(name=RoleType.STUDENT)
        db.add(role)
        db.commit()
        db.refresh(role)
    
    role_user = RoleUser(user_id=new_user.id, role_id=role.id)
    db.add(role_user)
    
    new_student = Student(
        user_id=new_user.id,
        student_number=student.student_number,
        date_of_birth=student.date_of_birth,
        grade_level=student.grade_level,
        address=student.address,
        emergency_contact=student.emergency_contact
    )
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    
    return StudentResponse(
        id=new_student.id,
        firstName=new_user.firstName,
        lastName=new_user.lastName,
        email=new_user.email,
        student_number=new_student.student_number,
        date_of_birth=new_student.date_of_birth.isoformat(),
        grade_level=new_student.grade_level,
        class_id=new_student.class_id
    )

@router.get("", response_model=List[StudentResponse])
async def get_students(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    students = db.query(Student).offset(skip).limit(limit).all()
    result = []
    for s in students:
        user = db.query(User).filter(User.id == s.user_id).first()
        result.append(StudentResponse(
            id=s.id,
            firstName=user.firstName,
            lastName=user.lastName,
            email=user.email,
            student_number=s.student_number,
            date_of_birth=s.date_of_birth.isoformat() if isinstance(s.date_of_birth, date) else str(s.date_of_birth),
            grade_level=s.grade_level,
            class_id=s.class_id
        ))
    return result

@router.get("/me")
async def get_my_student_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    
    user = db.query(User).filter(User.id == student.user_id).first()
    
    return {
        "id": student.id,
        "firstName": user.firstName,
        "lastName": user.lastName,
        "email": user.email,
        "student_number": student.student_number,
        "date_of_birth": str(student.date_of_birth),
        "grade_level": student.grade_level.value if hasattr(student.grade_level, 'value') else str(student.grade_level),
        "class_id": student.class_id
    }

@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    user = db.query(User).filter(User.id == student.user_id).first()
    return StudentResponse(
        id=student.id,
        firstName=user.firstName,
        lastName=user.lastName,
        email=user.email,
        student_number=student.student_number,
        date_of_birth=student.date_of_birth.isoformat() if isinstance(student.date_of_birth, date) else str(student.date_of_birth),
        grade_level=student.grade_level,
        class_id=student.class_id
    )

@router.delete("/{student_id}")
async def delete_student(
    student_id: int,
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db)
):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    db.delete(student)
    db.commit()
    return {"message": "Student deleted successfully"}

@router.get("/{student_id}/grades")
async def get_student_grades(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    grades = db.query(
        Grade,
        Course.name.label('course_name')
    ).join(Course, Grade.course_id == Course.id, isouter=True)\
     .filter(Grade.student_id == student_id).all()
    
    result = []
    for grade, course_name in grades:
        result.append({
            "id": grade.id,
            "course_id": grade.course_id,
            "course_name": course_name or "Unknown Course",
            "exam_id": grade.exam_id,
            "score": float(grade.score),
            "grade_value": grade.grade_value,
            "comments": grade.comments,
            "graded_at": grade.graded_at.isoformat() if grade.graded_at else None
        })
    
    return result

@router.get("/{student_id}/attendance")
async def get_student_attendance(
    student_id: int,
    date_from: date = None,
    date_to: date = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    query = db.query(Attendance).filter(Attendance.student_id == student_id)
    
    if date_from:
        query = query.filter(Attendance.date >= date_from)
    if date_to:
        query = query.filter(Attendance.date <= date_to)
    
    attendance_records = query.order_by(Attendance.date.desc()).all()
    
    return [{
        "id": a.id,
        "date": a.date,
        "status": a.status,
        "notes": a.notes
    } for a in attendance_records]

@router.get("/{student_id}/fees")
async def get_student_fees(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    fees = db.query(FeeRecord).filter(FeeRecord.student_id == student_id).all()
    
    return [{
        "id": f.id,
        "amount": f.amount,
        "fee_type": f.fee_type,
        "due_date": f.due_date,
        "paid_date": f.paid_date,
        "is_paid": f.is_paid,
        "payment_method": f.payment_method,
        "academic_year": f.academic_year
    } for f in fees]