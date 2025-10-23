from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional
from datetime import datetime
from utils.security import validate_password_strength

class UserCreate(BaseModel):
    email: EmailStr
    firstName: str = Field(..., min_length=1, max_length=50)
    lastName: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=8)
    role: str

    @field_validator('password')
    def password_strength(cls, v):
        if not validate_password_strength(v):
            raise ValueError(
                'Password must be at least 8 characters and contain '
                'uppercase, lowercase, digit, and special character'
            )
        return v

class RoleResponse(BaseModel):
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

class RoleUserResponse(BaseModel):
    assigned_at: datetime
    role: RoleResponse

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    roles: List[str]

    class Config:
        from_attributes = True
        populate_by_name = True

class UserInfoResponse(BaseModel):
    user: UserResponse

    class Config:
        from_attributes = True