from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import date, datetime

class AbsenceExcuseCreate(BaseModel):
    start_date: date = Field(..., description="Start date of absence")
    end_date: date = Field(..., description="End date of absence")
    reason: str = Field(..., description="Reason for absence (illness, medical_appointment, family_emergency, family_event, other)")
    message: str = Field(..., min_length=10, max_length=2000, description="Detailed message explaining the absence")
    
    @validator('end_date')
    def end_date_must_be_after_start_date(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('end_date must be on or after start_date')
        return v
    
    @validator('reason')
    def validate_reason(cls, v):
        valid_reasons = ['illness', 'medical_appointment', 'family_emergency', 'family_event', 'other']
        if v not in valid_reasons:
            raise ValueError(f'reason must be one of: {", ".join(valid_reasons)}')
        return v

class AbsenceExcuseUpdate(BaseModel):
    status: str = Field(..., description="New status (approved or rejected)")
    admin_notes: Optional[str] = Field(None, max_length=1000, description="Admin notes regarding the decision")
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ['approved', 'rejected']
        if v not in valid_statuses:
            raise ValueError(f'status must be one of: {", ".join(valid_statuses)}')
        return v

class AbsenceExcuseResponse(BaseModel):
    id: int
    student_id: int
    parent_id: int
    start_date: date
    end_date: date
    reason: str
    message: str
    status: str
    submitted_at: datetime
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[int]
    admin_notes: Optional[str]
    
    class Config:
        from_attributes = True

class AbsenceExcuseDetailResponse(BaseModel):
    id: int
    student_id: int
    student_name: str
    student_number: str
    parent_id: int
    parent_name: str
    start_date: date
    end_date: date
    reason: str
    message: str
    status: str
    submitted_at: datetime
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[str]
    admin_notes: Optional[str]
    
    class Config:
        from_attributes = True