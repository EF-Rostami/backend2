from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Enum, Boolean
from sqlalchemy.orm import relationship
from database import Base
import enum
from datetime import datetime

# Status of the appointment
class AppointmentStatus(enum.Enum):
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    REJECTED = "Rejected"
    CANCELLED = "Cancelled"

# Teacher availability table
class TeacherAvailability(Base):
    __tablename__ = "teacher_availabilities"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"))
    date = Column(DateTime, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    is_booked = Column(Boolean, default=False)

    teacher = relationship("User", backref="availabilities")

# Appointment table
class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("users.id"))
    availability_id = Column(Integer, ForeignKey("teacher_availabilities.id"))
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.PENDING)
    reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    parent = relationship("User", foreign_keys=[parent_id])
    availability = relationship("TeacherAvailability")

# Meeting summary table
class MeetingSummary(Base):
    __tablename__ = "meeting_summaries"

    id = Column(Integer, primary_key=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"))
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    appointment = relationship("Appointment", backref="summary")
