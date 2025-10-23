from pydantic import BaseModel, EmailStr
from typing import List

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class SessionInfo(BaseModel):
    active_sessions: int
    device_info: List[str]


class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str