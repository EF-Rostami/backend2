from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

# ==================== Event Schemas ====================

class EventCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    event_type: str = Field(..., description="Event type")
    start_date: datetime
    end_date: datetime
    location: Optional[str] = Field(None, max_length=255)
    target_audience: str = Field(default="all")
    target_grade_levels: Optional[str] = Field(None, description="Comma-separated grade levels")
    requires_rsvp: bool = Field(default=False)
    max_participants: Optional[int] = Field(None, gt=0)
    registration_deadline: Optional[datetime] = None
    organizer_name: Optional[str] = Field(None, max_length=255)
    organizer_contact: Optional[str] = Field(None, max_length=255)
    is_published: bool = Field(default=True)
    
    @validator('end_date')
    def end_date_after_start_date(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v
    
    @validator('event_type')
    def validate_event_type(cls, v):
        valid_types = ['assembly', 'meeting', 'sports', 'field_trip', 'holiday', 'exam', 'workshop', 'celebration', 'other']
        if v not in valid_types:
            raise ValueError(f'event_type must be one of: {", ".join(valid_types)}')
        return v
    
    @validator('target_audience')
    def validate_target_audience(cls, v):
        valid_audiences = ['all', 'students', 'parents', 'teachers', 'staff']
        if v not in valid_audiences:
            raise ValueError(f'target_audience must be one of: {", ".join(valid_audiences)}')
        return v

class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    event_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    location: Optional[str] = Field(None, max_length=255)
    target_audience: Optional[str] = None
    target_grade_levels: Optional[str] = None
    requires_rsvp: Optional[bool] = None
    max_participants: Optional[int] = Field(None, gt=0)
    registration_deadline: Optional[datetime] = None
    organizer_name: Optional[str] = Field(None, max_length=255)
    organizer_contact: Optional[str] = Field(None, max_length=255)
    is_published: Optional[bool] = None

class EventCancel(BaseModel):
    cancellation_reason: str = Field(..., min_length=10, max_length=1000)

class EventResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    event_type: str
    start_date: datetime
    end_date: datetime
    location: Optional[str]
    target_audience: str
    target_grade_levels: Optional[str]
    requires_rsvp: bool
    max_participants: Optional[int]
    registration_deadline: Optional[datetime]
    created_by: int
    organizer_name: Optional[str]
    organizer_contact: Optional[str]
    is_published: bool
    is_cancelled: bool
    cancellation_reason: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class EventDetailResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    event_type: str
    start_date: datetime
    end_date: datetime
    location: Optional[str]
    target_audience: str
    target_grade_levels: Optional[str]
    requires_rsvp: bool
    max_participants: Optional[int]
    registration_deadline: Optional[datetime]
    created_by: int
    creator_name: str
    organizer_name: Optional[str]
    organizer_contact: Optional[str]
    is_published: bool
    is_cancelled: bool
    cancellation_reason: Optional[str]
    created_at: datetime
    updated_at: datetime
    total_rsvps: int
    attending_count: int
    available_spots: Optional[int]
    user_rsvp_status: Optional[str]
    
    class Config:
        from_attributes = True

# ==================== RSVP Schemas ====================

class RSVPCreate(BaseModel):
    status: str = Field(..., description="RSVP status: attending, not_attending, maybe")
    student_id: Optional[int] = Field(None, description="Student ID if RSVP for a student")
    notes: Optional[str] = Field(None, max_length=500)
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ['attending', 'not_attending', 'maybe']
        if v not in valid_statuses:
            raise ValueError(f'status must be one of: {", ".join(valid_statuses)}')
        return v

class RSVPUpdate(BaseModel):
    status: str = Field(..., description="RSVP status: attending, not_attending, maybe")
    notes: Optional[str] = Field(None, max_length=500)
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ['attending', 'not_attending', 'maybe']
        if v not in valid_statuses:
            raise ValueError(f'status must be one of: {", ".join(valid_statuses)}')
        return v

class RSVPResponse(BaseModel):
    id: int
    event_id: int
    user_id: int
    student_id: Optional[int]
    status: str
    response_date: datetime
    notes: Optional[str]
    user_name: Optional[str]
    student_name: Optional[str]
    
    class Config:
        from_attributes = True

# ==================== Attachment Schemas ====================

class AttachmentResponse(BaseModel):
    id: int
    event_id: int
    file_name: str
    file_size: Optional[int]
    uploaded_by: int
    uploader_name: str
    uploaded_at: datetime
    
    class Config:
        from_attributes = True