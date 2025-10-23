
# ============================================================
# models/registration.py
# ============================================================
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base
from utils.enums import GradeLevel, RegistrationStatus

class RegistrationRequest(Base):
    __tablename__ = "registration_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    student_firstName = Column(String, nullable=False)
    student_lastName = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    desired_grade_level = Column(SQLEnum(GradeLevel), nullable=False)
    parent_firstName = Column(String, nullable=False)
    parent_lastName = Column(String, nullable=False)
    parent_email = Column(String, nullable=False)
    parent_phone = Column(String, nullable=False)
    address = Column(String, nullable=False)
    status = Column(SQLEnum(RegistrationStatus), default=RegistrationStatus.PENDING)
    submitted_at = Column(DateTime, default=datetime.now(timezone.utc))
    documents = Column(Text)
    
    approval_logs = relationship("RegistrationApprovalLog", back_populates="registration")

class RegistrationApprovalLog(Base):
    __tablename__ = "registration_approval_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    registration_id = Column(Integer, ForeignKey("registration_requests.id"))
    approved_by = Column(Integer, ForeignKey("users.id"))
    action = Column(String, nullable=False)
    comments = Column(Text)
    action_date = Column(DateTime, default=datetime.utcnow)
    
    registration = relationship("RegistrationRequest", back_populates="approval_logs")