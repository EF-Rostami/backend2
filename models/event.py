from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, Text, Boolean, Date
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base
from enum import Enum

class EventType(str, Enum):
    ASSEMBLY = "assembly"
    MEETING = "meeting"
    SPORTS = "sports"
    FIELD_TRIP = "field_trip"
    HOLIDAY = "holiday"
    EXAM = "exam"
    WORKSHOP = "workshop"
    CELEBRATION = "celebration"
    OTHER = "other"

class EventAudience(str, Enum):
    ALL = "all"
    STUDENTS = "students"
    PARENTS = "parents"
    TEACHERS = "teachers"
    STAFF = "staff"

class RSVPStatus(str, Enum):
    PENDING = "pending"
    ATTENDING = "attending"
    NOT_ATTENDING = "not_attending"
    MAYBE = "maybe"

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    event_type = Column(SQLEnum(EventType), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    location = Column(String(255), nullable=True)
    
    # Target audience
    target_audience = Column(SQLEnum(EventAudience), nullable=False, default=EventAudience.ALL)
    target_grade_levels = Column(String(500), nullable=True)  # Comma-separated grade levels
    
    # Registration settings
    requires_rsvp = Column(Boolean, default=False)
    max_participants = Column(Integer, nullable=True)
    registration_deadline = Column(DateTime(timezone=True), nullable=True)
    
    # Organizer
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    organizer_name = Column(String(255), nullable=True)
    organizer_contact = Column(String(255), nullable=True)
    
    # Status
    is_published = Column(Boolean, default=True)
    is_cancelled = Column(Boolean, default=False)
    cancellation_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    rsvps = relationship("EventRSVP", back_populates="event", cascade="all, delete-orphan")
    attachments = relationship("EventAttachment", back_populates="event", cascade="all, delete-orphan")

class EventRSVP(Base):
    __tablename__ = "event_rsvps"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)  # If RSVP for a student
    status = Column(SQLEnum(RSVPStatus), nullable=False, default=RSVPStatus.PENDING)
    response_date = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    notes = Column(Text, nullable=True)
    
    # Relationships
    event = relationship("Event", back_populates="rsvps")
    user = relationship("User")
    student = relationship("Student")

class EventAttachment(Base):
    __tablename__ = "event_attachments"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    
    # Relationships
    event = relationship("Event", back_populates="attachments")
    uploader = relationship("User")