from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from dependencies import get_current_user, require_roles
from models import User, Course
from schemas.academic import CourseCreate, CourseResponse

router = APIRouter(prefix="/courses", tags=["courses"])

@router.post("", response_model=CourseResponse)
async def create_course(
    course: CourseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_course = Course(
        name=course.name,
        code=course.code,
        description=course.description,
        class_id=course.class_id,
        teacher_id=course.teacher_id,
        academic_year=course.academic_year
    )
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    
    return CourseResponse(
        id=new_course.id,
        name=new_course.name,
        code=new_course.code,
        description=new_course.description,
        class_id=new_course.class_id,
        teacher_id=new_course.teacher_id,
        academic_year=new_course.academic_year
    )

@router.get("", response_model=List[CourseResponse])
async def get_courses(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    courses = db.query(Course).offset(skip).limit(limit).all()
    return [CourseResponse(
        id=c.id,
        name=c.name,
        code=c.code,
        description=c.description,
        class_id=c.class_id,
        teacher_id=c.teacher_id,
        academic_year=c.academic_year
    ) for c in courses]

@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    return CourseResponse(
        id=course.id,
        name=course.name,
        code=course.code,
        description=course.description,
        class_id=course.class_id,
        teacher_id=course.teacher_id,
        academic_year=course.academic_year
    )

@router.delete("/{course_id}")
async def delete_course(
    course_id: int,
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db)
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    db.delete(course)
    db.commit()
    return {"message": "Course deleted successfully"}