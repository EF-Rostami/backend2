
# ============================================================
# models/fees.py
# ============================================================
from sqlalchemy import Column, Integer, Float, String, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class FeeRecord(Base):
    __tablename__ = "fee_records"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    amount = Column(Float, nullable=False)
    fee_type = Column(String, nullable=False)
    due_date = Column(Date, nullable=False)
    paid_date = Column(Date)
    is_paid = Column(Boolean, default=False)
    payment_method = Column(String)
    academic_year = Column(String, nullable=False)
    
    student = relationship("Student", back_populates="fees")

