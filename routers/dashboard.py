from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from database import get_db
from dependencies import get_current_user
from models import (
    User, Student, Teacher, Class, Course, 
    RegistrationRequest, Attendance, FeeRecord, Grade
)
from utils.enums import RegistrationStatus, AttendanceStatus

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    total_students = db.query(Student).count()
    total_teachers = db.query(Teacher).count()
    total_classes = db.query(Class).count()
    total_courses = db.query(Course).count()
    pending_registrations = db.query(RegistrationRequest).filter(
        RegistrationRequest.status == RegistrationStatus.PENDING
    ).count()
    
    return {
        "total_students": total_students,
        "total_teachers": total_teachers,
        "total_classes": total_classes,
        "total_courses": total_courses,
        "pending_registrations": pending_registrations
    }

@router.get("/attendance-summary")
async def get_attendance_summary(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Attendance)
    
    if date_from:
        query = query.filter(Attendance.date >= date_from)
    if date_to:
        query = query.filter(Attendance.date <= date_to)
    
    attendance_records = query.all()
    
    present = sum(1 for a in attendance_records if a.status == AttendanceStatus.PRESENT)
    absent = sum(1 for a in attendance_records if a.status == AttendanceStatus.ABSENT)
    late = sum(1 for a in attendance_records if a.status == AttendanceStatus.LATE)
    excused = sum(1 for a in attendance_records if a.status == AttendanceStatus.EXCUSED)
    
    return {
        "total_records": len(attendance_records),
        "present": present,
        "absent": absent,
        "late": late,
        "excused": excused,
        "attendance_rate": round((present / len(attendance_records) * 100), 2) if attendance_records else 0
    }

@router.get("/fee-summary")
async def get_fee_summary(
    academic_year: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(FeeRecord)
    
    if academic_year:
        query = query.filter(FeeRecord.academic_year == academic_year)
    
    fees = query.all()
    
    total_fees = sum(f.amount for f in fees)
    paid_fees = sum(f.amount for f in fees if f.is_paid)
    unpaid_fees = total_fees - paid_fees
    
    return {
        "total_fees": total_fees,
        "paid_fees": paid_fees,
        "unpaid_fees": unpaid_fees,
        "total_records": len(fees),
        "paid_count": sum(1 for f in fees if f.is_paid),
        "unpaid_count": sum(1 for f in fees if not f.is_paid),
        "payment_rate": round((paid_fees / total_fees * 100), 2) if total_fees > 0 else 0
    }

@router.get("/grade-distribution")
async def get_grade_distribution(
    course_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Grade)
    
    if course_id:
        query = query.filter(Grade.course_id == course_id)
    
    grades = query.all()
    
    grade_counts = {}
    for g in grades:
        if g.grade_value:
            grade_counts[g.grade_value] = grade_counts.get(g.grade_value, 0) + 1
    
    average_score = sum(g.score for g in grades) / len(grades) if grades else 0
    
    return {
        "total_grades": len(grades),
        "average_score": round(average_score, 2),
        "grade_distribution": grade_counts
    }