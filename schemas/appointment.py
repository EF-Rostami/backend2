from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class AppointmentStatus(str, Enum):
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    REJECTED = "Rejected"
    CANCELLED = "Cancelled"

class TeacherAvailabilityCreate(BaseModel):
    date: datetime
    start_time: datetime
    end_time: datetime

class AppointmentCreate(BaseModel):
    availability_id: int
    reason: str | None = None

class MeetingSummaryCreate(BaseModel):
    appointment_id: int
    notes: str
