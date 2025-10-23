# ============================================================
# models/attendance.py
# ============================================================
from sqlalchemy import Column, Integer, Date, ForeignKey, Text, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base
from utils.enums import AttendanceStatus

class Attendance(Base):
    __tablename__ = "attendance"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    date = Column(Date, nullable=False)
    status = Column(SQLEnum(AttendanceStatus), nullable=False)
    notes = Column(Text)
    recorded_by = Column(Integer, ForeignKey("users.id"))
    recorded_at = Column(DateTime, default=datetime.now(timezone.utc))
    
    student = relationship("Student", back_populates="attendance")

