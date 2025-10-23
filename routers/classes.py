from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from dependencies import get_current_user, require_roles
from models import User, Class, Student, Course
from schemas.academic import ClassCreate, ClassResponse

router = APIRouter(prefix="/classes", tags=["classes"])

@router.post("", response_model=ClassResponse)
async def create_class(
    class_data: ClassCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_class = Class(
        name=class_data.name,
        grade_level=class_data.grade_level,
        academic_year=class_data.academic_year,
        class_teacher_id=class_data.class_teacher_id,
        room_number=class_data.room_number,
        max_students=class_data.max_students
    )
    db.add(new_class)
    db.commit()
    db.refresh(new_class)
    
    return ClassResponse(
        id=new_class.id,
        name=new_class.name,
        grade_level=new_class.grade_level,
        academic_year=new_class.academic_year,
        room_number=new_class.room_number,
        max_students=new_class.max_students
    )

@router.get("")
async def get_classes(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    classes = db.query(Class).offset(skip).limit(limit).all()
    
    result = []
    for c in classes:
        student_count = db.query(Student).filter(Student.class_id == c.id).count()
        
        result.append({
            "id": c.id,
            "name": c.name,
            "grade_level": c.grade_level,
            "academic_year": c.academic_year,
            "room_number": c.room_number,
            "max_students": c.max_students,
            "student_count": student_count
        })
    
    return result

@router.get("/{class_id}")
async def get_class(
    class_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")
    
    student_count = db.query(Student).filter(Student.class_id == class_id).count()
    
    return {
        "id": class_obj.id,
        "name": class_obj.name,
        "grade_level": class_obj.grade_level,
        "academic_year": class_obj.academic_year,
        "room_number": class_obj.room_number,
        "max_students": class_obj.max_students,
        "student_count": student_count
    }

@router.delete("/{class_id}")
async def delete_class(
    class_id: int,
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db)
):
    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")
    
    db.delete(class_obj)
    db.commit()
    return {"message": "Class deleted successfully"}

@router.get("/{class_id}/students")
async def get_class_students(
    class_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")
    
    students = db.query(Student).filter(Student.class_id == class_id).all()
    
    result = []
    for s in students:
        user = db.query(User).filter(User.id == s.user_id).first()
        result.append({
            "id": s.id,
            "firstName": user.firstName,
            "lastName": user.lastName,
            "student_number": s.student_number,
            "grade_level": s.grade_level
        })
    
    return result

@router.get("/{class_id}/courses")
async def get_class_courses(
    class_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")
    
    courses = db.query(Course).filter(Course.class_id == class_id).all()
    
    result = []
    for c in courses:
        from models import Teacher
        teacher = db.query(Teacher).filter(Teacher.id == c.teacher_id).first()
        teacher_user = db.query(User).filter(User.id == teacher.user_id).first() if teacher else None
        
        result.append({
            "id": c.id,
            "name": c.name,
            "code": c.code,
            "teacher_name": f"{teacher_user.firstName} {teacher_user.lastName}" if teacher_user else None
        })
    
    return result

@router.post("/{class_id}/students/{student_id}")
async def assign_student_to_class(
    class_id: int,
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")
    
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    current_students = db.query(Student).filter(Student.class_id == class_id).count()
    if current_students >= class_obj.max_students:
        raise HTTPException(status_code=400, detail="Class is full")
    
    student.class_id = class_id
    db.commit()
    
    return {"message": "Student assigned to class successfully"}

@router.delete("/{class_id}/students/{student_id}")
async def remove_student_from_class(
    class_id: int,
    student_id: int,
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db)
):
    student = db.query(Student).filter(Student.id == student_id, Student.class_id == class_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found in this class")
    
    student.class_id = None
    db.commit()
    
    return {"message": "Student removed from class successfully"}