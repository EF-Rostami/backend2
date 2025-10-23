from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from dependencies import get_current_user
from models import User, Role, RoleUser, Parent, Student, StudentParent
from schemas.student import ParentResponse
from utils.security import get_password_hash
from utils.enums import RoleType

router = APIRouter(prefix="/parents", tags=["parents"])

@router.post("", response_model=dict)
async def create_parent(
    firstName: str,
    lastName: str,
    email: str,
    password: str,
    phone_number: Optional[str] = None,
    address: Optional[str] = None,
    occupation: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    hashed_password = get_password_hash(password)
    new_user = User(
        email=email,
        firstName=firstName,
        lastName=lastName,
        password_hash=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    role = db.query(Role).filter(Role.name == RoleType.PARENT).first()
    if not role:
        role = Role(name=RoleType.PARENT)
        db.add(role)
        db.commit()
        db.refresh(role)
    
    role_user = RoleUser(user_id=new_user.id, role_id=role.id)
    db.add(role_user)
    
    new_parent = Parent(
        user_id=new_user.id,
        phone_number=phone_number,
        address=address,
        occupation=occupation
    )
    db.add(new_parent)
    db.commit()
    db.refresh(new_parent)
    
    return {"message": "Parent created successfully", "parent_id": new_parent.id}

@router.get("/me", response_model=ParentResponse)
async def get_my_parent_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    parent = db.query(Parent).filter(Parent.user_id == current_user.id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent profile not found")
    
    user = db.query(User).filter(User.id == parent.user_id).first()
    return ParentResponse(
        id=parent.id,
        firstName=user.firstName,
        lastName=user.lastName,
        email=user.email,
        phone_number=parent.phone_number,
        address=parent.address
    )

@router.post("/{parent_id}/students/{student_id}")
async def link_parent_to_student(
    parent_id: int,
    student_id: int,
    relationship_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    parent = db.query(Parent).filter(Parent.id == parent_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")
    
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    existing = db.query(StudentParent).filter(
        StudentParent.parent_id == parent_id,
        StudentParent.student_id == student_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Relationship already exists")
    
    student_parent = StudentParent(
        student_id=student_id,
        parent_id=parent_id,
        relationship_type=relationship_type
    )
    db.add(student_parent)
    db.commit()
    
    return {"message": "Parent linked to student successfully"}

@router.get("/{parent_id}/students")
async def get_parent_children(
    parent_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    parent = db.query(Parent).filter(Parent.id == parent_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")
    
    relationships = db.query(StudentParent).filter(StudentParent.parent_id == parent_id).all()
    
    result = []
    for rel in relationships:
        student = db.query(Student).filter(Student.id == rel.student_id).first()
        user = db.query(User).filter(User.id == student.user_id).first()
        
        result.append({
            "student_id": student.id,
            "firstName": user.firstName,
            "lastName": user.lastName,
            "student_number": student.student_number,
            "grade_level": student.grade_level,
            "relationship_type": rel.relationship_type
        })
    
    return result