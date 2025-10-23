from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime
from utils.enums import GradeLevel, RegistrationStatus

# Admission Letter Schemas
class AdmissionLetterCreate(BaseModel):
    admission_number: str
    child_first_name: str
    child_last_name: str
    grade_level: GradeLevel
    academic_year: str

class AdmissionLetterResponse(BaseModel):
    id: int
    admission_number: str
    child_first_name: str
    child_last_name: str
    grade_level: GradeLevel
    academic_year: str
    is_used: bool
    used_at: Optional[datetime]
    created_at: datetime
    created_by: int

    class Config:
        from_attributes = True

class BulkAdmissionLetterCreate(BaseModel):
    letters: List[AdmissionLetterCreate]

class BulkAdmissionLetterResponse(BaseModel):
    success_count: int
    error_count: int
    created_letters: List[AdmissionLetterResponse]
    errors: List[dict]

# Public Registration Schemas
class AdmissionVerifyRequest(BaseModel):
    admission_number: str
    child_first_name: str
    child_last_name: str

class AdmissionVerifyResponse(BaseModel):
    valid: bool
    admission_number: str
    child_first_name: str
    child_last_name: str
    grade_level: GradeLevel
    academic_year: str

class ParentAdmissionCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    mobile: str
    relation_type: str
    is_primary_contact: bool = False

class AdmissionRegisterRequest(BaseModel):
    admission_number: str
    student_first_name: str
    student_last_name: str
    date_of_birth: date
    place_of_birth: str
    nationality: str
    address_street: str
    address_city: str
    address_postal_code: str
    address_state: str = "Germany"
    parents: List[ParentAdmissionCreate]

class AdmissionRegisterResponse(BaseModel):
    success: bool
    admission_id: int
    admission_number: str
    status: RegistrationStatus
    message: str

class AdmissionStatusResponse(BaseModel):
    admission_number: str
    student_first_name: str
    student_last_name: str
    status: RegistrationStatus
    submitted_at: datetime
    approved_at: Optional[datetime]

class ParentAdmissionResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    mobile: str
    relation_type: str
    is_primary_contact: bool
    user_id: Optional[int]
    
    class Config:
        from_attributes = True

class StudentAdmissionResponse(BaseModel):
    id: int
    admission_number: str
    student_first_name: str
    student_last_name: str
    date_of_birth: date
    place_of_birth: Optional[str]
    nationality: Optional[str]
    grade_level: GradeLevel
    address_street: str
    address_city: str
    address_postal_code: str
    address_state: str
    status: RegistrationStatus
    submitted_at: datetime
    approved_at: Optional[datetime]
    approved_by: Optional[int]
    rejection_reason: Optional[str]
    parents: List[ParentAdmissionResponse]
    
    class Config:
        from_attributes = True

# Admin Approval/Rejection Schemas
class AdmissionApprovalRequest(BaseModel):
    admission_id: int

class AdmissionApprovalResponse(BaseModel):
    success: bool
    admission_id: int
    student_user_id: int
    parent_user_ids: List[int]
    student_username: str
    parent_usernames: List[str]
    message: str

class AdmissionRejectionRequest(BaseModel):
    admission_id: int
    reason: str

class AdmissionRejectionResponse(BaseModel):
    success: bool
    admission_id: int
    message: str