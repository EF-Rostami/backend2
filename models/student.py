from sqlalchemy import Column, Integer, String, Date, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base
from utils.enums import GradeLevel

class Student(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    student_number = Column(String, unique=True, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    grade_level = Column(SQLEnum(GradeLevel), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"))
    enrollment_date = Column(Date, default=datetime.now(timezone.utc))
    address = Column(String)
    emergency_contact = Column(String)
    
    user = relationship("User")
    class_obj = relationship("Class", back_populates="students")
    parents = relationship("StudentParent", back_populates="student")
    grades = relationship("Grade", back_populates="student")
    attendance = relationship("Attendance", back_populates="student")
    fees = relationship("FeeRecord", back_populates="student")

class Parent(Base):
    __tablename__ = "parents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    phone_number = Column(String)
    address = Column(String)
    occupation = Column(String)
    
    user = relationship("User")
    children = relationship("StudentParent", back_populates="parent")

class StudentParent(Base):
    __tablename__ = "student_parents"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    parent_id = Column(Integer, ForeignKey("parents.id"))
    relationship_type = Column(String)
    
    student = relationship("Student", back_populates="parents")
    parent = relationship("Parent", back_populates="children")