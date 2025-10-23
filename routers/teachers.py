from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from dependencies import get_current_user, require_roles
from models import User, Role, RoleUser, Teacher, Course, Class
from schemas.teacher import TeacherCreate, TeacherResponse
from utils.security import get_password_hash
from utils.enums import RoleType

router = APIRouter(prefix="/teachers", tags=["teachers"])

@router.post("", response_model=TeacherResponse)
async def create_teacher(
    teacher: TeacherCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    hashed_password = get_password_hash(teacher.password)
    new_user = User(
        email=teacher.email,
        firstName=teacher.firstName,
        lastName=teacher.lastName,
        password_hash=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    role = db.query(Role).filter(Role.name == RoleType.TEACHER).first()
    if not role:
        role = Role(name=RoleType.TEACHER)
        db.add(role)
        db.commit()
        db.refresh(role)
    
    role_user = RoleUser(user_id=new_user.id, role_id=role.id)
    db.add(role_user)
    
    new_teacher = Teacher(
        user_id=new_user.id,
        employee_number=teacher.employee_number,
        subject_specialization=teacher.subject_specialization,
        phone_number=teacher.phone_number
    )
    db.add(new_teacher)
    db.commit()
    db.refresh(new_teacher)
    
    return TeacherResponse(
        id=new_teacher.id,
        firstName=new_user.firstName,
        lastName=new_user.lastName,
        email=new_user.email,
        employee_number=new_teacher.employee_number,
        subject_specialization=new_teacher.subject_specialization
    )

@router.get("", response_model=List[TeacherResponse])
async def get_teachers(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    teachers = db.query(Teacher).offset(skip).limit(limit).all()
    result = []
    for t in teachers:
        user = db.query(User).filter(User.id == t.user_id).first()
        result.append(TeacherResponse(
            id=t.id,
            firstName=user.firstName,
            lastName=user.lastName,
            email=user.email,
            employee_number=t.employee_number,
            subject_specialization=t.subject_specialization
        ))
    return result

@router.get("/me", response_model=TeacherResponse)
async def get_my_teacher_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher profile not found")
    
    user = db.query(User).filter(User.id == teacher.user_id).first()
    return TeacherResponse(
        id=teacher.id,
        firstName=user.firstName,
        lastName=user.lastName,
        email=user.email,
        employee_number=teacher.employee_number,
        subject_specialization=teacher.subject_specialization
    )

@router.get("/{teacher_id}", response_model=TeacherResponse)
async def get_teacher(
    teacher_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    user = db.query(User).filter(User.id == teacher.user_id).first()
    return TeacherResponse(
        id=teacher.id,
        firstName=user.firstName,
        lastName=user.lastName,
        email=user.email,
        employee_number=teacher.employee_number,
        subject_specialization=teacher.subject_specialization
    )

@router.delete("/{teacher_id}")
async def delete_teacher(
    teacher_id: int,
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db)
):
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    db.delete(teacher)
    db.commit()
    return {"message": "Teacher deleted successfully"}

@router.get("/{teacher_id}/courses")
async def get_teacher_courses(
    teacher_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    courses = db.query(Course).filter(Course.teacher_id == teacher_id).all()
    
    result = []
    for c in courses:
        class_obj = db.query(Class).filter(Class.id == c.class_id).first()
        
        result.append({
            "id": c.id,
            "name": c.name,
            "code": c.code,
            "class_name": class_obj.name if class_obj else None,
            "academic_year": c.academic_year
        })
    
    return result

@router.get("/{teacher_id}/classes")
async def get_teacher_classes(
    teacher_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    from models import Student
    classes = db.query(Class).filter(Class.class_teacher_id == teacher_id).all()
    
    result = []
    for c in classes:
        student_count = db.query(Student).filter(Student.class_id == c.id).count()
        
        result.append({
            "id": c.id,
            "name": c.name,
            "grade_level": c.grade_level,
            "room_number": c.room_number,
            "student_count": student_count,
            "max_students": c.max_students
        })
    
    return result