from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base
from utils.enums import GradeLevel, RegistrationStatus

class AdmissionLetter(Base):
    __tablename__ = "admission_letters"
    
    id = Column(Integer, primary_key=True, index=True)
    admission_number = Column(String, unique=True, nullable=False, index=True)
    child_first_name = Column(String, nullable=False)
    child_last_name = Column(String, nullable=False)
    grade_level = Column(SQLEnum(GradeLevel), nullable=False)
    academic_year = Column(String, nullable=False)
    is_used = Column(Boolean, default=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    created_by = Column(Integer, ForeignKey("users.id"))
    
    student_admission = relationship("StudentAdmission", back_populates="admission_letter", uselist=False)

class StudentAdmission(Base):
    __tablename__ = "student_admissions"
    
    id = Column(Integer, primary_key=True, index=True)
    admission_letter_id = Column(Integer, ForeignKey("admission_letters.id"), unique=True)
    admission_number = Column(String, unique=True, nullable=False)
    
    # Student Information
    student_first_name = Column(String, nullable=False)
    student_last_name = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    place_of_birth = Column(String)
    nationality = Column(String)
    grade_level = Column(SQLEnum(GradeLevel), nullable=False)
    
    # Address
    address_street = Column(String, nullable=False)
    address_city = Column(String, nullable=False)
    address_postal_code = Column(String, nullable=False)
    address_state = Column(String, default="Germany")
    
    # Status
    status = Column(SQLEnum(RegistrationStatus), default=RegistrationStatus.PENDING)
    submitted_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Relationships
    admission_letter = relationship("AdmissionLetter", back_populates="student_admission")
    parents = relationship("ParentAdmission", back_populates="student_admission")

class ParentAdmission(Base):
    __tablename__ = "parent_admissions"
    
    id = Column(Integer, primary_key=True, index=True)
    student_admission_id = Column(Integer, ForeignKey("student_admissions.id"))
    
    # Parent Information
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False, index=True)
    mobile = Column(String, nullable=False)
    occupation = Column(Boolean, nullable=True)
    relation_type = Column(String, nullable=False)  # mother, father, guardian
    is_primary_contact = Column(Boolean, default=False)
    
    # Account (created after approval)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationship
    student_admission = relationship("StudentAdmission", back_populates="parents")