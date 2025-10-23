from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from dependencies import get_current_user, require_roles
from models import User, Grade, Course
from schemas.academic import GradeCreate, GradeResponse

router = APIRouter(prefix="/grades", tags=["grades"])

@router.post("", response_model=GradeResponse)
async def create_grade(
    grade: GradeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_grade = Grade(
        student_id=grade.student_id,
        course_id=grade.course_id,
        exam_id=grade.exam_id,
        score=grade.score,
        grade_value=grade.grade_value,
        comments=grade.comments
    )
    db.add(new_grade)
    db.commit()
    db.refresh(new_grade)
    
    return GradeResponse(
        id=new_grade.id,
        student_id=new_grade.student_id,
        course_id=new_grade.course_id,
        exam_id=new_grade.exam_id,
        score=new_grade.score,
        grade_value=new_grade.grade_value
    )

@router.get("")
async def get_grades(
    skip: int = 0,
    limit: int = 100,
    student_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(
        Grade,
        Course.name.label('course_name')
    ).join(Course, Grade.course_id == Course.id)
    
    if student_id:
        query = query.filter(Grade.student_id == student_id)
    
    grades = query.offset(skip).limit(limit).all()
    
    result = []
    for grade, course_name in grades:
        result.append({
            "id": grade.id,
            "student_id": grade.student_id,
            "course_id": grade.course_id,
            "course_name": course_name,
            "exam_id": grade.exam_id,
            "score": float(grade.score),
            "grade_value": grade.grade_value,
            "comments": grade.comments,
            "graded_at": grade.graded_at.isoformat() if grade.graded_at else None
        })
    
    return result

@router.get("/{grade_id}", response_model=GradeResponse)
async def get_grade(
    grade_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    grade = db.query(Grade).filter(Grade.id == grade_id).first()
    if not grade:
        raise HTTPException(status_code=404, detail="Grade not found")
    
    return GradeResponse(
        id=grade.id,
        student_id=grade.student_id,
        course_id=grade.course_id,
        exam_id=grade.exam_id,
        score=grade.score,
        grade_value=grade.grade_value
    )

@router.delete("/{grade_id}")
async def delete_grade(
    grade_id: int,
    current_user: User = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db)
):
    grade = db.query(Grade).filter(Grade.id == grade_id).first()
    if not grade:
        raise HTTPException(status_code=404, detail="Grade not found")
    
    db.delete(grade)
    db.commit()
    return {"message": "Grade deleted successfully"}