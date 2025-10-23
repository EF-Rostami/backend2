# ============================================================
# schemas/attendance.py
# ============================================================
from pydantic import BaseModel
from typing import Optional
from datetime import date
from utils.enums import AttendanceStatus

class AttendanceCreate(BaseModel):
    student_id: int
    date: date
    status: AttendanceStatus
    notes: Optional[str] = None

class AttendanceResponse(BaseModel):
    id: int
    student_id: int
    date: date
    status: AttendanceStatus
    notes: Optional[str]
    
    class Config:
        from_attributes = True

