from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from database import get_db
from dependencies import get_current_user, require_roles, get_user_roles
from models import User, Student, Parent, StudentParent, AbsenceExcuse
from schemas.absence_excuse import (
    AbsenceExcuseCreate,
    AbsenceExcuseUpdate,
    AbsenceExcuseResponse,
    AbsenceExcuseDetailResponse
)

router = APIRouter(prefix="/absence-excuses", tags=["absence-excuses"])

# ================== PARENT ENDPOINTS ==================

@router.post("/students/{student_id}/absence-excuses", response_model=AbsenceExcuseResponse)
async def create_absence_excuse(
    student_id: int,
    excuse_data: AbsenceExcuseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Parent submits an absence excuse for their child.
    """
    # Get parent record
    parent = db.query(Parent).filter(Parent.user_id == current_user.id).first()
    if not parent:
        raise HTTPException(status_code=403, detail="You must be a parent to submit excuses")
    
    # Verify student exists
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Verify parent-student relationship
    relationship = db.query(StudentParent).filter(
        StudentParent.student_id == student_id,
        StudentParent.parent_id == parent.id
    ).first()
    
    if not relationship:
        raise HTTPException(status_code=403, detail="You are not authorized to submit excuses for this student")
    
    # Create the excuse
    new_excuse = AbsenceExcuse(
        student_id=student_id,
        parent_id=parent.id,
        start_date=excuse_data.start_date,
        end_date=excuse_data.end_date,
        reason=excuse_data.reason,
        message=excuse_data.message,
        status="pending"
    )
    
    db.add(new_excuse)
    db.commit()
    db.refresh(new_excuse)
    
    return AbsenceExcuseResponse(
        id=new_excuse.id,
        student_id=new_excuse.student_id,
        parent_id=new_excuse.parent_id,
        start_date=new_excuse.start_date,
        end_date=new_excuse.end_date,
        reason=new_excuse.reason.value if hasattr(new_excuse.reason, 'value') else new_excuse.reason,
        message=new_excuse.message,
        status=new_excuse.status.value if hasattr(new_excuse.status, 'value') else new_excuse.status,
        submitted_at=new_excuse.submitted_at,
        reviewed_at=new_excuse.reviewed_at,
        reviewed_by=new_excuse.reviewed_by,
        admin_notes=new_excuse.admin_notes
    )

@router.get("/students/{student_id}/absence-excuses", response_model=List[AbsenceExcuseResponse])
async def get_student_absence_excuses(
    student_id: int,
    status: Optional[str] = Query(None, description="Filter by status: pending, approved, rejected"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all absence excuses for a specific student.
    Parents can only see their own children's excuses.
    Admins and teachers can see all excuses.
    """
    user_roles = get_user_roles(current_user)
    
    # Check authorization
    if "parent" in user_roles:
        parent = db.query(Parent).filter(Parent.user_id == current_user.id).first()
        if not parent:
            raise HTTPException(status_code=403, detail="Parent profile not found")
        
        # Verify parent-student relationship
        relationship = db.query(StudentParent).filter(
            StudentParent.student_id == student_id,
            StudentParent.parent_id == parent.id
        ).first()
        
        if not relationship:
            raise HTTPException(status_code=403, detail="You are not authorized to view excuses for this student")
    
    elif "admin" not in user_roles and "teacher" not in user_roles:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Query excuses
    query = db.query(AbsenceExcuse).filter(AbsenceExcuse.student_id == student_id)
    
    if status:
        query = query.filter(AbsenceExcuse.status == status)
    
    excuses = query.order_by(AbsenceExcuse.submitted_at.desc()).all()
    
    result = []
    for excuse in excuses:
        result.append(AbsenceExcuseResponse(
            id=excuse.id,
            student_id=excuse.student_id,
            parent_id=excuse.parent_id,
            start_date=excuse.start_date,
            end_date=excuse.end_date,
            reason=excuse.reason.value if hasattr(excuse.reason, 'value') else excuse.reason,
            message=excuse.message,
            status=excuse.status.value if hasattr(excuse.status, 'value') else excuse.status,
            submitted_at=excuse.submitted_at,
            reviewed_at=excuse.reviewed_at,
            reviewed_by=excuse.reviewed_by,
            admin_notes=excuse.admin_notes
        ))
    
    return result

# ================== ADMIN/TEACHER ENDPOINTS ==================

@router.get("", response_model=List[AbsenceExcuseDetailResponse])
async def get_all_absence_excuses(
    status: Optional[str] = Query(None, description="Filter by status: pending, approved, rejected"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db)
):
    """
    Get all absence excuses (admin/teacher only).
    """
    query = db.query(AbsenceExcuse)
    
    if status:
        query = query.filter(AbsenceExcuse.status == status)
    
    excuses = query.order_by(AbsenceExcuse.submitted_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for excuse in excuses:
        # Get student info
        student = db.query(Student).filter(Student.id == excuse.student_id).first()
        student_user = db.query(User).filter(User.id == student.user_id).first() if student else None
        
        # Get parent info
        parent = db.query(Parent).filter(Parent.id == excuse.parent_id).first()
        parent_user = db.query(User).filter(User.id == parent.user_id).first() if parent else None
        
        # Get reviewer info
        reviewer_name = None
        if excuse.reviewed_by:
            reviewer = db.query(User).filter(User.id == excuse.reviewed_by).first()
            if reviewer:
                reviewer_name = f"{reviewer.firstName} {reviewer.lastName}"
        
        result.append(AbsenceExcuseDetailResponse(
            id=excuse.id,
            student_id=excuse.student_id,
            student_name=f"{student_user.firstName} {student_user.lastName}" if student_user else "Unknown",
            student_number=student.student_number if student else "N/A",
            parent_id=excuse.parent_id,
            parent_name=f"{parent_user.firstName} {parent_user.lastName}" if parent_user else "Unknown",
            start_date=excuse.start_date,
            end_date=excuse.end_date,
            reason=excuse.reason.value if hasattr(excuse.reason, 'value') else excuse.reason,
            message=excuse.message,
            status=excuse.status.value if hasattr(excuse.status, 'value') else excuse.status,
            submitted_at=excuse.submitted_at,
            reviewed_at=excuse.reviewed_at,
            reviewed_by=reviewer_name,
            admin_notes=excuse.admin_notes
        ))
    
    return result

@router.get("/{excuse_id}", response_model=AbsenceExcuseDetailResponse)
async def get_absence_excuse_detail(
    excuse_id: int,
    current_user: User = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific absence excuse (admin/teacher only).
    """
    excuse = db.query(AbsenceExcuse).filter(AbsenceExcuse.id == excuse_id).first()
    if not excuse:
        raise HTTPException(status_code=404, detail="Absence excuse not found")
    
    # Get student info
    student = db.query(Student).filter(Student.id == excuse.student_id).first()
    student_user = db.query(User).filter(User.id == student.user_id).first() if student else None
    
    # Get parent info
    parent = db.query(Parent).filter(Parent.id == excuse.parent_id).first()
    parent_user = db.query(User).filter(User.id == parent.user_id).first() if parent else None
    
    # Get reviewer info
    reviewer_name = None
    if excuse.reviewed_by:
        reviewer = db.query(User).filter(User.id == excuse.reviewed_by).first()
        if reviewer:
            reviewer_name = f"{reviewer.firstName} {reviewer.lastName}"
    
    return AbsenceExcuseDetailResponse(
        id=excuse.id,
        student_id=excuse.student_id,
        student_name=f"{student_user.firstName} {student_user.lastName}" if student_user else "Unknown",
        student_number=student.student_number if student else "N/A",
        parent_id=excuse.parent_id,
        parent_name=f"{parent_user.firstName} {parent_user.lastName}" if parent_user else "Unknown",
        start_date=excuse.start_date,
        end_date=excuse.end_date,
        reason=excuse.reason.value if hasattr(excuse.reason, 'value') else excuse.reason,
        message=excuse.message,
        status=excuse.status.value if hasattr(excuse.status, 'value') else excuse.status,
        submitted_at=excuse.submitted_at,
        reviewed_at=excuse.reviewed_at,
        reviewed_by=reviewer_name,
        admin_notes=excuse.admin_notes
    )

@router.patch("/{excuse_id}", response_model=AbsenceExcuseDetailResponse)
async def update_absence_excuse_status(
    excuse_id: int,
    update_data: AbsenceExcuseUpdate,
    current_user: User = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db)
):
    """
    Approve or reject an absence excuse (admin/teacher only).
    """
    excuse = db.query(AbsenceExcuse).filter(AbsenceExcuse.id == excuse_id).first()
    if not excuse:
        raise HTTPException(status_code=404, detail="Absence excuse not found")
    
    # Update the excuse
    excuse.status = update_data.status
    excuse.reviewed_at = datetime.now(timezone.utc)
    excuse.reviewed_by = current_user.id
    
    if update_data.admin_notes:
        excuse.admin_notes = update_data.admin_notes
    
    db.commit()
    db.refresh(excuse)
    
    # Get student info
    student = db.query(Student).filter(Student.id == excuse.student_id).first()
    student_user = db.query(User).filter(User.id == student.user_id).first() if student else None
    
    # Get parent info
    parent = db.query(Parent).filter(Parent.id == excuse.parent_id).first()
    parent_user = db.query(User).filter(User.id == parent.user_id).first() if parent else None
    
    # Get reviewer info
    reviewer_name = f"{current_user.firstName} {current_user.lastName}"
    
    return AbsenceExcuseDetailResponse(
        id=excuse.id,
        student_id=excuse.student_id,
        student_name=f"{student_user.firstName} {student_user.lastName}" if student_user else "Unknown",
        student_number=student.student_number if student else "N/A",
        parent_id=excuse.parent_id,
        parent_name=f"{parent_user.firstName} {parent_user.lastName}" if parent_user else "Unknown",
        start_date=excuse.start_date,
        end_date=excuse.end_date,
        reason=excuse.reason.value if hasattr(excuse.reason, 'value') else excuse.reason,
        message=excuse.message,
        status=excuse.status.value if hasattr(excuse.status, 'value') else excuse.status,
        submitted_at=excuse.submitted_at,
        reviewed_at=excuse.reviewed_at,
        reviewed_by=reviewer_name,
        admin_notes=excuse.admin_notes
    )

@router.delete("/{excuse_id}")
async def delete_absence_excuse(
    excuse_id: int,
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db)
):
    """
    Delete an absence excuse (admin only).
    """
    excuse = db.query(AbsenceExcuse).filter(AbsenceExcuse.id == excuse_id).first()
    if not excuse:
        raise HTTPException(status_code=404, detail="Absence excuse not found")
    
    db.delete(excuse)
    db.commit()
    
    return {"message": "Absence excuse deleted successfully"}