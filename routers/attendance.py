from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from database import get_db
from dependencies import get_current_user, require_roles
from models import User, Attendance
from schemas.attendance import AttendanceCreate, AttendanceResponse

router = APIRouter(prefix="/attendance", tags=["attendance"])

@router.post("", response_model=AttendanceResponse)
async def create_attendance(
    attendance: AttendanceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_attendance = Attendance(
        student_id=attendance.student_id,
        date=attendance.date,
        status=attendance.status,
        notes=attendance.notes,
        recorded_by=current_user.id
    )
    db.add(new_attendance)
    db.commit()
    db.refresh(new_attendance)
    
    return AttendanceResponse(
        id=new_attendance.id,
        student_id=new_attendance.student_id,
        date=new_attendance.date,
        status=new_attendance.status,
        notes=new_attendance.notes
    )

@router.get("", response_model=List[AttendanceResponse])
async def get_attendance(
    skip: int = 0,
    limit: int = 100,
    student_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Attendance)
    if student_id:
        query = query.filter(Attendance.student_id == student_id)
    
    attendance_records = query.offset(skip).limit(limit).all()
    return [AttendanceResponse(
        id=a.id,
        student_id=a.student_id,
        date=a.date,
        status=a.status,
        notes=a.notes
    ) for a in attendance_records]

@router.get("/{attendance_id}", response_model=AttendanceResponse)
async def get_attendance_record(
    attendance_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    attendance = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    
    return AttendanceResponse(
        id=attendance.id,
        student_id=attendance.student_id,
        date=attendance.date,
        status=attendance.status,
        notes=attendance.notes
    )

@router.delete("/{attendance_id}")
async def delete_attendance(
    attendance_id: int,
    current_user: User = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db)
):
    attendance = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    
    db.delete(attendance)
    db.commit()
    return {"message": "Attendance record deleted successfully"}