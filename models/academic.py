from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base
from utils.enums import GradeLevel

class Class(Base):
    __tablename__ = "classes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    grade_level = Column(SQLEnum(GradeLevel), nullable=False)
    academic_year = Column(String, nullable=False)
    class_teacher_id = Column(Integer, ForeignKey("teachers.id"))
    room_number = Column(String)
    max_students = Column(Integer, default=25)
    
    class_teacher = relationship("Teacher", back_populates="classes")
    students = relationship("Student", back_populates="class_obj")
    courses = relationship("Course", back_populates="class_obj")

class Course(Base):
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)
    description = Column(Text)
    class_id = Column(Integer, ForeignKey("classes.id"))
    teacher_id = Column(Integer, ForeignKey("teachers.id"))
    academic_year = Column(String, nullable=False)
    
    class_obj = relationship("Class", back_populates="courses")
    teacher = relationship("Teacher", back_populates="courses")
    exams = relationship("Exam", back_populates="course")
    grades = relationship("Grade", back_populates="course")

class Exam(Base):
    __tablename__ = "exams"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    class_id = Column(Integer, ForeignKey("classes.id"))
    title = Column(String, nullable=False)
    exam_date = Column(Date, nullable=False)
    max_score = Column(Float, nullable=False)
    description = Column(Text)
    subject = Column(String)
    exam_type = Column(String, default='written')
    weight = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    
    course = relationship("Course", back_populates="exams")
    class_obj = relationship("Class")
    grades = relationship("Grade", back_populates="exam")

class Grade(Base):
    __tablename__ = "grades"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    exam_id = Column(Integer, ForeignKey("exams.id"))
    score = Column(Float, nullable=False)
    grade_value = Column(String)
    comments = Column(Text)
    graded_at = Column(DateTime, default=datetime.now(timezone.utc))
    
    student = relationship("Student", back_populates="grades")
    course = relationship("Course", back_populates="grades")
    exam = relationship("Exam", back_populates="grades")