from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

# Import your SQLAlchemy models
from database import get_db
from dependencies import get_current_user
from repositories.appointment import book_appointment, confirm_appointment, create_availability, save_meeting_summary
from models import TeacherAvailability, Appointment, MeetingSummary, AppointmentStatus

# Import your Pydantic schemas
from schemas import TeacherAvailabilityCreate, AppointmentCreate, MeetingSummaryCreate

router = APIRouter(prefix="/appointments", tags=["Appointments"])




@router.post("/teacher/availability")
def add_availability(data: TeacherAvailabilityCreate, current_user=Depends(get_current_user), db=Depends(get_db)):
    if current_user.role != "teacher":
        raise HTTPException(403)
    return create_availability(db, current_user.id, data)

@router.get("/available")
def list_available_slots(class_id: int, db=Depends(get_db)):
    # Filter by class and teacher's availability
    return db.query(TeacherAvailability).filter(TeacherAvailability.is_booked==False).all()

@router.post("/book")
def book_slot(data: AppointmentCreate, current_user=Depends(get_current_user), db=Depends(get_db)):
    if current_user.role != "parent":
        raise HTTPException(403)
    return book_appointment(db, current_user.id, data.availability_id, data.reason)

@router.patch("/confirm/{appointment_id}")
def confirm(appointment_id: int, current_user=Depends(get_current_user), db=Depends(get_db)):
    if current_user.role != "teacher":
        raise HTTPException(403)
    return confirm_appointment(db, appointment_id)

@router.post("/summary")
def save_summary(data: MeetingSummaryCreate, current_user=Depends(get_current_user), db=Depends(get_db)):
    if current_user.role != "teacher":
        raise HTTPException(403)
    return save_meeting_summary(db, data.appointment_id, data.notes)

