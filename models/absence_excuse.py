from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base
from enum import Enum

class ExcuseStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class AbsenceReason(str, Enum):
    ILLNESS = "illness"
    MEDICAL_APPOINTMENT = "medical_appointment"
    FAMILY_EMERGENCY = "family_emergency"
    FAMILY_EVENT = "family_event"
    OTHER = "other"

class AbsenceExcuse(Base):
    __tablename__ = "absence_excuses"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("parents.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(SQLEnum(AbsenceReason), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(SQLEnum(ExcuseStatus), default=ExcuseStatus.PENDING, nullable=False)
    submitted_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    admin_notes = Column(Text, nullable=True)
    
    # Relationships
    student = relationship("Student", foreign_keys=[student_id])
    parent = relationship("Parent", foreign_keys=[parent_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])