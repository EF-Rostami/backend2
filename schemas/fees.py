
# ============================================================
# schemas/fees.py
# ============================================================
from pydantic import BaseModel
from datetime import date

class FeeRecordCreate(BaseModel):
    student_id: int
    amount: float
    fee_type: str
    due_date: date
    academic_year: str

class FeeRecordResponse(BaseModel):
    id: int
    student_id: int
    amount: float
    fee_type: str
    due_date: date
    is_paid: bool
    academic_year: str
    
    class Config:
        from_attributes = True

