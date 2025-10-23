from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timezone

from database import get_db
from dependencies import get_current_user, require_roles
from models import User, Exam, Grade, Class
from schemas.academic import ExamCreate, ExamResponse

router = APIRouter(prefix="/exams", tags=["exams"])

@router.post("", response_model=ExamResponse)
async def create_exam(
    exam: ExamCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_exam = Exam(
        course_id=exam.course_id,
        class_id=exam.class_id,
        title=exam.title,
        exam_date=exam.exam_date,
        max_score=exam.max_score,
        subject=exam.subject,
        exam_type=exam.exam_type,
        weight=exam.weight,
        description=exam.description
    )
    db.add(new_exam)
    db.commit()
    db.refresh(new_exam)
    
    return ExamResponse(
        id=new_exam.id,
        title=new_exam.title,
        exam_date=new_exam.exam_date,
        max_score=new_exam.max_score,
        subject=new_exam.subject,
        exam_type=new_exam.exam_type,
        weight=new_exam.weight,
        course_id=new_exam.course_id,
        class_id=new_exam.class_id,
        description=new_exam.description
    )

@router.get("", response_model=List[ExamResponse])
async def get_exams(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    exams = db.query(Exam).offset(skip).limit(limit).all()
    return [ExamResponse(
        id=e.id,
        title=e.title,
        exam_date=e.exam_date,
        max_score=e.max_score,
        subject=e.subject or '',
        exam_type=e.exam_type or 'written',
        weight=e.weight or 1.0,
        course_id=e.course_id,
        class_id=e.class_id,
        description=e.description
    ) for e in exams]

@router.get("/{exam_id}", response_model=ExamResponse)
async def get_exam(
    exam_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    return ExamResponse(
        id=exam.id,
        title=exam.title,
        exam_date=exam.exam_date,
        max_score=exam.max_score,
        subject=exam.subject or '',
        exam_type=exam.exam_type or 'written',
        weight=exam.weight or 1.0,
        course_id=exam.course_id,
        class_id=exam.class_id,
        description=exam.description
    )

@router.delete("/{exam_id}")
async def delete_exam(
    exam_id: int,
    current_user: User = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db)
):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    db.delete(exam)
    db.commit()
    return {"message": "Exam deleted successfully"}

@router.get("/classes/{class_id}/exams", response_model=List[ExamResponse])
async def get_class_exams(
    class_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all exams for a specific class"""
    exams = db.query(Exam).filter(Exam.class_id == class_id).order_by(Exam.exam_date.desc()).all()
    return [ExamResponse(
        id=e.id,
        title=e.title,
        exam_date=e.exam_date,
        max_score=e.max_score,
        subject=e.subject or '',
        exam_type=e.exam_type or 'written',
        weight=e.weight or 1.0,
        course_id=e.course_id,
        class_id=e.class_id,
        description=e.description
    ) for e in exams]

@router.post("/classes/{class_id}/exams", response_model=ExamResponse)
async def create_class_exam(
    class_id: int,
    exam: ExamCreate,
    current_user: User = Depends(require_roles(["teacher", "admin"])),
    db: Session = Depends(get_db)
):
    """Create an exam for a specific class"""
    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")
    
    new_exam = Exam(
        class_id=class_id,
        course_id=exam.course_id,
        title=exam.title,
        exam_date=exam.exam_date,
        max_score=exam.max_score,
        subject=exam.subject,
        exam_type=exam.exam_type,
        weight=exam.weight,
        description=exam.description
    )
    db.add(new_exam)
    db.commit()
    db.refresh(new_exam)
    
    return ExamResponse(
        id=new_exam.id,
        title=new_exam.title,
        exam_date=new_exam.exam_date,
        max_score=new_exam.max_score,
        subject=new_exam.subject,
        exam_type=new_exam.exam_type,
        weight=new_exam.weight,
        course_id=new_exam.course_id,
        class_id=new_exam.class_id,
        description=new_exam.description
    )

# Exam Results Schemas
class ExamResultInput(BaseModel):
    student_id: int
    score: float
    notes: Optional[str] = None

class ExamResultsInput(BaseModel):
    results: List[ExamResultInput]

@router.get("/{exam_id}/results")
async def get_exam_results(
    exam_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all results for a specific exam"""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    grades = db.query(Grade).filter(Grade.exam_id == exam_id).all()
    
    return [{
        "student_id": g.student_id,
        "score": g.score,
        "grade_value": g.grade_value,
        "notes": g.comments
    } for g in grades]

@router.post("/{exam_id}/results")
async def save_exam_results(
    exam_id: int,
    data: ExamResultsInput,
    current_user: User = Depends(require_roles(["teacher", "admin"])),
    db: Session = Depends(get_db)
):
    """Save or update exam results for multiple students"""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    for result in data.results:
        existing_grade = db.query(Grade).filter(
            Grade.exam_id == exam_id,
            Grade.student_id == result.student_id
        ).first()
        
        # Calculate grade value (German grading system)
        percentage = (result.score / exam.max_score) * 100
        if percentage >= 92:
            grade_value = "1"  # Sehr gut
        elif percentage >= 81:
            grade_value = "2"  # Gut
        elif percentage >= 67:
            grade_value = "3"  # Befriedigend
        elif percentage >= 50:
            grade_value = "4"  # Ausreichend
        elif percentage >= 30:
            grade_value = "5"  # Mangelhaft
        else:
            grade_value = "6"  # Ungenügend
        
        if existing_grade:
            existing_grade.score = result.score
            existing_grade.grade_value = grade_value
            existing_grade.comments = result.notes
            existing_grade.graded_at = datetime.now(timezone.utc)
        else:
            new_grade = Grade(
                student_id=result.student_id,
                course_id=exam.course_id,
                exam_id=exam_id,
                score=result.score,
                grade_value=grade_value,
                comments=result.notes
            )
            db.add(new_grade)
    
    db.commit()
    return {"message": "Results saved successfully", "count": len(data.results)}