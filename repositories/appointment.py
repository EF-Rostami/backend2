# repositories/appointment.py

from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

# Import your SQLAlchemy models
from models import TeacherAvailability, Appointment, MeetingSummary, AppointmentStatus

# Import your Pydantic schemas
from schemas import TeacherAvailabilityCreate, AppointmentCreate, MeetingSummaryCreate


# -------------------------------
# Teacher Availability CRUD
# -------------------------------
def create_availability(db: Session, teacher_id: int, data: TeacherAvailabilityCreate):
    availability = TeacherAvailability(
        teacher_id=teacher_id,
        date=data.date,
        start_time=data.start_time,
        end_time=data.end_time,
        is_booked=False
    )
    db.add(availability)
    db.commit()
    db.refresh(availability)
    return availability


def get_teacher_availabilities(db: Session, teacher_id: int):
    return db.query(TeacherAvailability).filter(TeacherAvailability.teacher_id == teacher_id).all()


def get_available_slots(db: Session, class_id: Optional[int] = None):
    # Optional: filter by class if needed
    return db.query(TeacherAvailability).filter(TeacherAvailability.is_booked == False).all()


# -------------------------------
# Appointment CRUD
# -------------------------------
def book_appointment(db: Session, parent_id: int, availability_id: int, reason: Optional[str] = None):
    availability = db.query(TeacherAvailability).filter(
        TeacherAvailability.id == availability_id,
        TeacherAvailability.is_booked == False
    ).first()
    if not availability:
        raise Exception("Selected time slot is not available")

    appointment = Appointment(
        parent_id=parent_id,
        availability_id=availability_id,
        status=AppointmentStatus.PENDING,
        reason=reason
    )
    availability.is_booked = True
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


def get_teacher_appointments(db: Session, teacher_id: int):
    return db.query(Appointment).join(TeacherAvailability).filter(
        TeacherAvailability.teacher_id == teacher_id
    ).all()


def update_appointment_status(db: Session, appointment_id: int, status: AppointmentStatus):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise Exception("Appointment not found")
    appointment.status = status
    db.commit()
    db.refresh(appointment)
    return appointment


def confirm_appointment(db, appointment_id: int):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if appointment:
        appointment.status = AppointmentStatus.CONFIRMED
        db.commit()
        db.refresh(appointment)
    return appointment


# -------------------------------
# Meeting Summary CRUD
# -------------------------------
def save_meeting_summary(db: Session, appointment_id: int, notes: str):
    summary = MeetingSummary(
        appointment_id=appointment_id,
        notes=notes
    )
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return summary


def get_meeting_summary(db: Session, appointment_id: int):
    return db.query(MeetingSummary).filter(MeetingSummary.appointment_id == appointment_id).first()
