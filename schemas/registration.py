
# ============================================================
# schemas/registration.py
# ============================================================
from pydantic import BaseModel, EmailStr
from datetime import date
from utils.enums import GradeLevel, RegistrationStatus

class RegistrationRequestCreate(BaseModel):
    student_firstName: str
    student_lastName: str
    date_of_birth: date
    desired_grade_level: GradeLevel
    parent_firstName: str
    parent_lastName: str
    parent_email: EmailStr
    parent_phone: str
    address: str

class RegistrationRequestResponse(BaseModel):
    id: int
    student_firstName: str
    student_lastName: str
    date_of_birth: date
    desired_grade_level: GradeLevel
    parent_email: str
    status: RegistrationStatus
    
    class Config:
        from_attributes = True