from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime, timezone, date
import os

from database import get_db
from dependencies import get_current_user, require_roles
from models import (
    User, Role, RoleUser, Student, Parent, StudentParent,
    AdmissionLetter, StudentAdmission, ParentAdmission
)
from schemas.admission import (
    AdmissionLetterCreate, AdmissionLetterResponse,
    BulkAdmissionLetterCreate, BulkAdmissionLetterResponse,
    AdmissionVerifyRequest, AdmissionVerifyResponse,
    AdmissionRegisterRequest, AdmissionRegisterResponse,
    AdmissionStatusResponse, StudentAdmissionResponse,
    AdmissionApprovalRequest, AdmissionApprovalResponse,
    AdmissionRejectionRequest, AdmissionRejectionResponse
)
from utils.enums import RoleType, RegistrationStatus
from utils.security import get_password_hash, generate_password
from services.email_service import (
    send_admission_pending_email,
    send_admission_approval_email,
    send_admission_rejection_email
)
from services.admission_service import generate_admission_number

router = APIRouter(prefix="/admission", tags=["admission"])

# ============================================================================
# ADMIN ENDPOINTS - Generate & Manage Admission Letters
# ============================================================================

@router.post("/letters", response_model=AdmissionLetterResponse)
async def create_admission_letter(
    letter: AdmissionLetterCreate,
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db)
):
    """Create a single admission letter (Admin only)"""
    
    existing = db.query(AdmissionLetter).filter(
        AdmissionLetter.admission_number == letter.admission_number
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Admission number {letter.admission_number} already exists"
        )
    
    db_letter = AdmissionLetter(
        admission_number=letter.admission_number,
        child_first_name=letter.child_first_name,
        child_last_name=letter.child_last_name,
        grade_level=letter.grade_level,
        academic_year=letter.academic_year,
        is_used=False,
        created_by=current_user.id
    )
    
    db.add(db_letter)
    db.commit()
    db.refresh(db_letter)
    
    return db_letter

@router.post("/letters/bulk", response_model=BulkAdmissionLetterResponse)
async def create_bulk_admission_letters(
    bulk_data: BulkAdmissionLetterCreate,
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db)
):
    """Create multiple admission letters at once (Admin only)"""
    
    created_letters = []
    errors = []
    
    for idx, letter_data in enumerate(bulk_data.letters):
        try:
            existing = db.query(AdmissionLetter).filter(
                AdmissionLetter.admission_number == letter_data.admission_number
            ).first()
            
            if existing:
                errors.append({
                    "index": idx,
                    "admission_number": letter_data.admission_number,
                    "error": "Admission number already exists"
                })
                continue
            
            db_letter = AdmissionLetter(
                admission_number=letter_data.admission_number,
                child_first_name=letter_data.child_first_name,
                child_last_name=letter_data.child_last_name,
                grade_level=letter_data.grade_level,
                academic_year=letter_data.academic_year,
                is_used=False,
                created_by=current_user.id
            )
            
            db.add(db_letter)
            created_letters.append(db_letter)
            
        except Exception as e:
            errors.append({
                "index": idx,
                "admission_number": letter_data.admission_number,
                "error": str(e)
            })
    
    if created_letters:
        db.commit()
        for letter in created_letters:
            db.refresh(letter)
    
    return {
        "success_count": len(created_letters),
        "error_count": len(errors),
        "created_letters": created_letters,
        "errors": errors
    }

@router.get("/letters", response_model=List[AdmissionLetterResponse])
async def get_admission_letters(
    skip: int = 0,
    limit: int = 100,
    grade_level: Optional[str] = None,
    academic_year: Optional[str] = None,
    is_used: Optional[bool] = None,
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db)
):
    """Get all admission letters with optional filters (Admin only)"""
    
    query = db.query(AdmissionLetter)
    
    if grade_level:
        query = query.filter(AdmissionLetter.grade_level == grade_level)
    if academic_year:
        query = query.filter(AdmissionLetter.academic_year == academic_year)
    if is_used is not None:
        query = query.filter(AdmissionLetter.is_used == is_used)
    
    query = query.order_by(AdmissionLetter.created_at.desc())
    
    letters = query.offset(skip).limit(limit).all()
    return letters

@router.get("/letters/{letter_id}", response_model=AdmissionLetterResponse)
async def get_admission_letter(
    letter_id: int,
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db)
):
    """Get specific admission letter by ID (Admin only)"""
    
    letter = db.query(AdmissionLetter).filter(AdmissionLetter.id == letter_id).first()
    
    if not letter:
        raise HTTPException(status_code=404, detail="Admission letter not found")
    
    return letter

# ============================================================================
# PUBLIC ENDPOINTS - Parent Registration
# ============================================================================

@router.post("/verify", response_model=AdmissionVerifyResponse)
async def verify_admission_letter(
    verify_data: AdmissionVerifyRequest,
    db: Session = Depends(get_db)
):
    """Verify admission number and child name (Public endpoint)"""
    
    letter = db.query(AdmissionLetter).filter(
        AdmissionLetter.admission_number == verify_data.admission_number
    ).first()
    
    if not letter:
        raise HTTPException(
            status_code=404,
            detail="Admission number not found. Please check your admission letter."
        )
    
    if letter.is_used:
        raise HTTPException(
            status_code=400,
            detail="This admission number has already been used for registration."
        )
    
    # Verify child name (case-insensitive)
    full_name_letter = f"{letter.child_first_name} {letter.child_last_name}".lower().strip()
    full_name_input = f"{verify_data.child_first_name} {verify_data.child_last_name}".lower().strip()
    
    if full_name_letter != full_name_input:
        raise HTTPException(
            status_code=400,
            detail="Child name does not match our records. Please check your admission letter."
        )
    
    return {
        "valid": True,
        "admission_number": letter.admission_number,
        "child_first_name": letter.child_first_name,
        "child_last_name": letter.child_last_name,
        "grade_level": letter.grade_level,
        "academic_year": letter.academic_year
    }

@router.post("/register", response_model=AdmissionRegisterResponse)
async def register_student_admission(
    registration: AdmissionRegisterRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Complete student admission registration (Public endpoint)"""
    
    letter = db.query(AdmissionLetter).filter(
        AdmissionLetter.admission_number == registration.admission_number
    ).first()
    
    if not letter:
        raise HTTPException(status_code=404, detail="Admission number not found")
    
    if letter.is_used:
        raise HTTPException(status_code=400, detail="Admission number already used")
    
    # Check if email already exists in pending or approved admissions
    for parent in registration.parents:
        existing_admission = db.query(ParentAdmission).filter(
            ParentAdmission.email == parent.email
        ).first()
        
        if existing_admission:
            raise HTTPException(
                status_code=400,
                detail=f"Email {parent.email} is already registered. Please use a different email."
            )
    
    # Create student admission record
    db_admission = StudentAdmission(
        admission_letter_id=letter.id,
        admission_number=letter.admission_number,
        student_first_name=registration.student_first_name,
        student_last_name=registration.student_last_name,
        date_of_birth=registration.date_of_birth,
        place_of_birth=registration.place_of_birth,
        nationality=registration.nationality,
        grade_level=letter.grade_level,
        address_street=registration.address_street,
        address_city=registration.address_city,
        address_postal_code=registration.address_postal_code,
        address_state=registration.address_state,
        status=RegistrationStatus.PENDING,
        submitted_at=datetime.now(timezone.utc)
    )
    
    db.add(db_admission)
    db.flush()
    
    # Create parent records
    for parent_data in registration.parents:
        db_parent = ParentAdmission(
            student_admission_id=db_admission.id,
            first_name=parent_data.first_name,
            last_name=parent_data.last_name,
            email=parent_data.email,
            mobile=parent_data.mobile,
            relation_type=parent_data.relation_type,
            is_primary_contact=parent_data.is_primary_contact
        )
        db.add(db_parent)
    
    # Mark admission letter as used
    letter.is_used = True
    letter.used_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(db_admission)
    
    # Send pending notification email
    primary_parent = next(
        (p for p in registration.parents if p.is_primary_contact),
        registration.parents[0]
    )
    
    try:
        await send_admission_pending_email(
            to_email=primary_parent.email,
            parent_name=f"{primary_parent.first_name} {primary_parent.last_name}",
            child_name=f"{registration.student_first_name} {registration.student_last_name}",
            admission_number=registration.admission_number
        )
    except Exception as e:
        print(f"Failed to send pending email: {str(e)}")
    
    return {
        "success": True,
        "admission_id": db_admission.id,
        "admission_number": db_admission.admission_number,
        "status": db_admission.status,
        "message": "Your admission has been submitted successfully. You will receive an email once it's reviewed."
    }

@router.get("/status/{admission_number}", response_model=AdmissionStatusResponse)
async def check_admission_status(
    admission_number: str,
    db: Session = Depends(get_db)
):
    """Check admission status by admission number (Public endpoint)"""
    
    admission = db.query(StudentAdmission).filter(
        StudentAdmission.admission_number == admission_number
    ).first()
    
    if not admission:
        raise HTTPException(
            status_code=404,
            detail="No registration found for this admission number"
        )
    
    return {
        "admission_number": admission.admission_number,
        "student_first_name": admission.student_first_name,
        "student_last_name": admission.student_last_name,
        "status": admission.status,
        "submitted_at": admission.submitted_at,
        "approved_at": admission.approved_at
    }

# ============================================================================
# ADMIN APPROVAL ENDPOINTS
# ============================================================================

@router.get("/pending", response_model=List[StudentAdmissionResponse])
async def get_pending_admissions(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db)
):
    """Get all pending admission registrations (Admin only)"""
    
    pending_admissions = db.query(StudentAdmission).options(
        joinedload(StudentAdmission.parents)
    ).filter(
        StudentAdmission.status == RegistrationStatus.PENDING
    ).order_by(StudentAdmission.submitted_at.desc()).offset(skip).limit(limit).all()
    
    return pending_admissions

@router.post("/approve", response_model=AdmissionApprovalResponse)
async def approve_admission(
    approval: AdmissionApprovalRequest,
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db)
):
    """Approve admission and create user accounts (Admin only)"""
    
    admission = db.query(StudentAdmission).options(
        joinedload(StudentAdmission.admission_letter),
        joinedload(StudentAdmission.parents)
    ).filter(StudentAdmission.id == approval.admission_id).first()
    
    if not admission:
        raise HTTPException(status_code=404, detail="Admission not found")
    
    if admission.status != RegistrationStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Admission is already {admission.status.value}"
        )
    
    try:
        primary_parent = next(
            (p for p in admission.parents if p.is_primary_contact),
            admission.parents[0] if admission.parents else None
        )
        
        if not primary_parent:
            raise HTTPException(status_code=400, detail="No parent information found")
        
        # Generate credentials
        student_password = generate_password(
            admission.student_first_name,
            admission.date_of_birth
        )
        
        # Create student user
        student_user = User(
            email=f"{admission.student_first_name.lower()}.{admission.student_last_name.lower()}@student.school.de",
            username=f"{admission.student_first_name.lower()}.{admission.student_last_name.lower()}",
            firstName=admission.student_first_name,
            lastName=admission.student_last_name,
            password_hash=get_password_hash(student_password),
            is_active=True,
            is_verified=True
        )
        db.add(student_user)
        db.flush()
        
        # Assign student role
        student_role = db.query(Role).filter(Role.name == RoleType.STUDENT).first()
        if not student_role:
            student_role = Role(name=RoleType.STUDENT, description="Student role")
            db.add(student_role)
            db.flush()
        
        role_user = RoleUser(user_id=student_user.id, role_id=student_role.id)
        db.add(role_user)
        
        # Create student profile
        student_profile = Student(
            user_id=student_user.id,
            student_number=admission.admission_number,
            date_of_birth=admission.date_of_birth,
            grade_level=admission.grade_level,
            enrollment_date=date.today()
        )
        db.add(student_profile)
        db.flush()
        
        # Create parent accounts
        parent_user_ids = []
        parent_credentials = []
        
        for parent_info in admission.parents:
            parent_password = generate_password(
                parent_info.first_name,
                admission.date_of_birth
            )
            
            existing_parent = db.query(User).filter(User.email == parent_info.email).first()
            
            if existing_parent:
                parent_user = existing_parent
            else:
                parent_user = User(
                    email=parent_info.email,
                    username=f"{parent_info.first_name.lower()}.{parent_info.last_name.lower()}.parent",
                    firstName=parent_info.first_name,
                    lastName=parent_info.last_name,
                    password_hash=get_password_hash(parent_password),
                    is_active=True,
                    is_verified=True
                )
                db.add(parent_user)
                db.flush()
                
                parent_role = db.query(Role).filter(Role.name == RoleType.PARENT).first()
                if not parent_role:
                    parent_role = Role(name=RoleType.PARENT, description="Parent role")
                    db.add(parent_role)
                    db.flush()
                
                role_user = RoleUser(user_id=parent_user.id, role_id=parent_role.id)
                db.add(role_user)
            
            parent_info.user_id = parent_user.id
            parent_user_ids.append(parent_user.id)
            parent_credentials.append({
                "email": parent_info.email,
                "password": parent_password
            })

            # Create parent profile
            parent_profile = Parent(
                user_id=parent_user.id,
                phone_number=parent_info.mobile,  # Changed from phone_number to mobile
                address=f"{admission.address_street}, {admission.address_city}, {admission.address_postal_code}",
                occupation=parent_info.occupation
                
            )
            db.add(parent_profile)
            db.flush()
        
                    
            # *** ADD THIS: Create student-parent relationship ***
            student_parent = StudentParent(
                student_id=student_profile.id,
                parent_id=parent_profile.id,
                relation_type=parent_info.relation_type,
                is_primary_contact=parent_info.is_primary_contact
            )
            db.add(student_parent)


        # Update admission status
        admission.status = RegistrationStatus.APPROVED
        admission.approved_at = datetime.now(timezone.utc)
        admission.approved_by = current_user.id
        
        if admission.admission_letter:
            admission.admission_letter.is_used = True
            admission.admission_letter.used_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(admission)
        
        # Send approval email
        try:
            await send_admission_approval_email(
                to_email=primary_parent.email,
                parent_name=f"{primary_parent.first_name} {primary_parent.last_name}",
                child_name=f"{admission.student_first_name} {admission.student_last_name}",
                admission_number=admission.admission_number,
                parent_username=primary_parent.email,
                parent_password=parent_credentials[0]["password"],
                student_username=student_user.username,
                student_password=student_password,
                portal_url=os.getenv("FRONTEND_URL", "http://localhost:3000")
            )
        except Exception as e:
            print(f"Failed to send approval email: {str(e)}")
        
        return AdmissionApprovalResponse(
            success=True,
            admission_id=admission.id,
            student_user_id=student_user.id,
            parent_user_ids=parent_user_ids,
            student_username=student_user.username,
            parent_usernames=[p["email"] for p in parent_credentials],
            message="Admission approved successfully"
        )
        
    except Exception as e:
        db.rollback()
        print(f"Approval error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to approve admission: {str(e)}")

@router.post("/reject", response_model=AdmissionRejectionResponse)
async def reject_admission(
    rejection: AdmissionRejectionRequest,
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db)
):
    """Reject admission registration (Admin only)"""
    
    admission = db.query(StudentAdmission).options(
        joinedload(StudentAdmission.parents)
    ).filter(
        StudentAdmission.id == rejection.admission_id
    ).first()
    
    if not admission:
        raise HTTPException(status_code=404, detail="Admission not found")
    
    if admission.status != RegistrationStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Admission is already {admission.status.value}"
        )
    
    # Update admission status
    admission.status = RegistrationStatus.REJECTED
    admission.approved_at = datetime.now(timezone.utc)
    admission.approved_by = current_user.id
    admission.rejection_reason = rejection.reason
    
    # Mark admission letter as not used (allow reuse if needed)
    if admission.admission_letter:
        admission.admission_letter.is_used = False
        admission.admission_letter.used_at = None
    
    db.commit()
    
    # Send rejection email
    primary_parent = next(
        (p for p in admission.parents if p.is_primary_contact),
        admission.parents[0] if admission.parents else None
    )
    
    if primary_parent:
        try:
            await send_admission_rejection_email(
                to_email=primary_parent.email,
                parent_name=f"{primary_parent.first_name} {primary_parent.last_name}",
                child_name=f"{admission.student_first_name} {admission.student_last_name}",
                admission_number=admission.admission_number,
                reason=rejection.reason
            )
        except Exception as e:
            print(f"Failed to send rejection email: {str(e)}")
    
    return {
        "success": True,
        "admission_id": admission.id,
        "message": "Admission rejected successfully. Notification sent to parent."
    }