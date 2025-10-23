from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from dependencies import get_current_user
from models import User, RegistrationRequest, RegistrationApprovalLog
from schemas.registration import RegistrationRequestCreate, RegistrationRequestResponse
from utils.enums import RegistrationStatus

router = APIRouter(prefix="/registrations", tags=["registrations"])

@router.post("", response_model=RegistrationRequestResponse)
async def create_registration_request(
    registration: RegistrationRequestCreate,
    db: Session = Depends(get_db)
):
    new_registration = RegistrationRequest(
        student_firstName=registration.student_firstName,
        student_lastName=registration.student_lastName,
        date_of_birth=registration.date_of_birth,
        desired_grade_level=registration.desired_grade_level,
        parent_firstName=registration.parent_firstName,
        parent_lastName=registration.parent_lastName,
        parent_email=registration.parent_email,
        parent_phone=registration.parent_phone,
        address=registration.address
    )
    db.add(new_registration)
    db.commit()
    db.refresh(new_registration)
    
    return RegistrationRequestResponse(
        id=new_registration.id,
        student_firstName=new_registration.student_firstName,
        student_lastName=new_registration.student_lastName,
        date_of_birth=new_registration.date_of_birth,
        desired_grade_level=new_registration.desired_grade_level,
        parent_email=new_registration.parent_email,
        status=new_registration.status
    )

@router.get("", response_model=List[RegistrationRequestResponse])
async def get_registration_requests(
    skip: int = 0,
    limit: int = 100,
    status: Optional[RegistrationStatus] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(RegistrationRequest)
    if status:
        query = query.filter(RegistrationRequest.status == status)
    
    registrations = query.offset(skip).limit(limit).all()
    return [RegistrationRequestResponse(
        id=r.id,
        student_firstName=r.student_firstName,
        student_lastName=r.student_lastName,
        date_of_birth=r.date_of_birth,
        desired_grade_level=r.desired_grade_level,
        parent_email=r.parent_email,
        status=r.status
    ) for r in registrations]

@router.get("/{registration_id}", response_model=RegistrationRequestResponse)
async def get_registration_request(
    registration_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    registration = db.query(RegistrationRequest).filter(RegistrationRequest.id == registration_id).first()
    if not registration:
        raise HTTPException(status_code=404, detail="Registration request not found")
    
    return RegistrationRequestResponse(
        id=registration.id,
        student_firstName=registration.student_firstName,
        student_lastName=registration.student_lastName,
        date_of_birth=registration.date_of_birth,
        desired_grade_level=registration.desired_grade_level,
        parent_email=registration.parent_email,
        status=registration.status
    )

@router.patch("/{registration_id}/approve")
async def approve_registration(
    registration_id: int,
    comments: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    registration = db.query(RegistrationRequest).filter(RegistrationRequest.id == registration_id).first()
    if not registration:
        raise HTTPException(status_code=404, detail="Registration request not found")
    
    registration.status = RegistrationStatus.APPROVED
    db.commit()
    
    approval_log = RegistrationApprovalLog(
        registration_id=registration_id,
        approved_by=current_user.id,
        action="approved",
        comments=comments
    )
    db.add(approval_log)
    db.commit()
    
    return {"message": "Registration approved successfully"}

@router.patch("/{registration_id}/reject")
async def reject_registration(
    registration_id: int,
    comments: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    registration = db.query(RegistrationRequest).filter(RegistrationRequest.id == registration_id).first()
    if not registration:
        raise HTTPException(status_code=404, detail="Registration request not found")
    
    registration.status = RegistrationStatus.REJECTED
    db.commit()
    
    approval_log = RegistrationApprovalLog(
        registration_id=registration_id,
        approved_by=current_user.id,
        action="rejected",
        comments=comments
    )
    db.add(approval_log)
    db.commit()
    
    return {"message": "Registration rejected successfully"}

@router.delete("/{registration_id}")
async def delete_registration(
    registration_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    registration = db.query(RegistrationRequest).filter(RegistrationRequest.id == registration_id).first()
    if not registration:
        raise HTTPException(status_code=404, detail="Registration request not found")
    
    db.delete(registration)
    db.commit()
    return {"message": "Registration request deleted successfully"}