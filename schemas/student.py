from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date
from utils.enums import GradeLevel

class StudentCreate(BaseModel):
    firstName: str
    lastName: str
    email: EmailStr
    password: str
    student_number: str
    date_of_birth: date
    grade_level: GradeLevel
    address: Optional[str] = None
    emergency_contact: Optional[str] = None

class StudentResponse(BaseModel):
    id: int
    firstName: str
    lastName: str
    email: str
    student_number: str
    date_of_birth: str
    grade_level: GradeLevel
    class_id: Optional[int]
    
    class Config:
        from_attributes = True

class ParentResponse(BaseModel):
    id: int
    firstName: str
    lastName: str
    email: str
    phone_number: Optional[str]
    address: Optional[str]
    
    class Config:
        from_attributes = True