from pydantic import BaseModel, EmailStr
from typing import Optional

class TeacherCreate(BaseModel):
    firstName: str
    lastName: str
    email: EmailStr
    password: str
    employee_number: str
    subject_specialization: Optional[str] = None
    phone_number: Optional[str] = None

class TeacherResponse(BaseModel):
    id: int
    firstName: str
    lastName: str
    email: str
    employee_number: str
    subject_specialization: Optional[str]
    
    class Config:
        from_attributes = True