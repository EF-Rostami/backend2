from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from utils.enums import GradeLevel

# ============================================================
# CLASS SCHEMAS
# ============================================================

class ClassCreate(BaseModel):
    name: str
    grade_level: GradeLevel
    academic_year: str
    class_teacher_id: Optional[int] = None
    room_number: Optional[str] = None
    max_students: int = 25

class ClassResponse(BaseModel):
    id: int
    name: str
    grade_level: GradeLevel
    academic_year: str
    room_number: Optional[str]
    max_students: int
    
    class Config:
        from_attributes = True

# ============================================================
# COURSE SCHEMAS
# ============================================================

class CourseCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    class_id: int
    teacher_id: int
    academic_year: str

class CourseResponse(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str]
    class_id: int
    teacher_id: int
    academic_year: str
    
    class Config:
        from_attributes = True

# ============================================================
# EXAM SCHEMAS
# ============================================================

class ExamCreate(BaseModel):
    title: str
    exam_date: date
    max_score: float
    subject: str
    exam_type: str = 'written'
    weight: float = 1.0
    description: Optional[str] = None
    course_id: Optional[int] = None
    class_id: int

class ExamResponse(BaseModel):
    id: int
    title: str
    exam_date: date
    max_score: float
    subject: str
    exam_type: str
    weight: float
    course_id: Optional[int]
    class_id: int
    description: Optional[str]
    
    class Config:
        from_attributes = True

# ============================================================
# GRADE SCHEMAS
# ============================================================

class GradeCreate(BaseModel):
    student_id: int
    course_id: int
    exam_id: int
    score: float
    grade_value: Optional[str] = None
    comments: Optional[str] = None

class GradeResponse(BaseModel):
    id: int
    student_id: int
    course_id: int
    exam_id: int
    score: float
    grade_value: Optional[str]
    
    class Config:
        from_attributes = True

class GradeWithDetailsResponse(BaseModel):
    id: int
    student_id: int
    course_id: int
    course_name: str
    exam_id: int
    score: float
    grade_value: Optional[str]
    comments: Optional[str]
    graded_at: datetime
    
    class Config:
        from_attributes = True