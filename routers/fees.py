from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from database import get_db
from dependencies import get_current_user, require_roles
from models import User, FeeRecord
from schemas.fees import FeeRecordCreate, FeeRecordResponse

router = APIRouter(prefix="/fees", tags=["fees"])

@router.post("", response_model=FeeRecordResponse)
async def create_fee(
    fee: FeeRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_fee = FeeRecord(
        student_id=fee.student_id,
        amount=fee.amount,
        fee_type=fee.fee_type,
        due_date=fee.due_date,
        academic_year=fee.academic_year
    )
    db.add(new_fee)
    db.commit()
    db.refresh(new_fee)
    
    return FeeRecordResponse(
        id=new_fee.id,
        student_id=new_fee.student_id,
        amount=new_fee.amount,
        fee_type=new_fee.fee_type,
        due_date=new_fee.due_date,
        is_paid=new_fee.is_paid,
        academic_year=new_fee.academic_year
    )

@router.get("", response_model=List[FeeRecordResponse])
async def get_fees(
    skip: int = 0,
    limit: int = 100,
    student_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(FeeRecord)
    if student_id:
        query = query.filter(FeeRecord.student_id == student_id)
    
    fees = query.offset(skip).limit(limit).all()
    return [FeeRecordResponse(
        id=f.id,
        student_id=f.student_id,
        amount=f.amount,
        fee_type=f.fee_type,
        due_date=f.due_date,
        is_paid=f.is_paid,
        academic_year=f.academic_year
    ) for f in fees]

@router.get("/{fee_id}", response_model=FeeRecordResponse)
async def get_fee(
    fee_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    fee = db.query(FeeRecord).filter(FeeRecord.id == fee_id).first()
    if not fee:
        raise HTTPException(status_code=404, detail="Fee record not found")
    
    return FeeRecordResponse(
        id=fee.id,
        student_id=fee.student_id,
        amount=fee.amount,
        fee_type=fee.fee_type,
        due_date=fee.due_date,
        is_paid=fee.is_paid,
        academic_year=fee.academic_year
    )

@router.patch("/{fee_id}/pay")
async def pay_fee(
    fee_id: int,
    payment_method: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    fee = db.query(FeeRecord).filter(FeeRecord.id == fee_id).first()
    if not fee:
        raise HTTPException(status_code=404, detail="Fee record not found")
    
    fee.is_paid = True
    fee.paid_date = datetime.now(timezone.utc).date()
    fee.payment_method = payment_method
    db.commit()
    
    return {"message": "Fee payment recorded successfully"}

@router.delete("/{fee_id}")
async def delete_fee(
    fee_id: int,
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db)
):
    fee = db.query(FeeRecord).filter(FeeRecord.id == fee_id).first()
    if not fee:
        raise HTTPException(status_code=404, detail="Fee record not found")
    
    db.delete(fee)
    db.commit()
    return {"message": "Fee record deleted successfully"}