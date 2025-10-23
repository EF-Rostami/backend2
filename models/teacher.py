from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base

class Teacher(Base):
    __tablename__ = "teachers"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    employee_number = Column(String, unique=True, nullable=False)
    subject_specialization = Column(String)
    hire_date = Column(Date, default=datetime.now(timezone.utc))
    phone_number = Column(String)
    
    user = relationship("User")
    courses = relationship("Course", back_populates="teacher")
    classes = relationship("Class", back_populates="class_teacher")