import secrets
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime, timezone, timedelta
import uuid

from models.auth import PasswordResetToken
from database import get_db
from dependencies import security, get_current_user, get_current_active_user
from models import User, Role, RoleUser, RefreshToken, TokenBlacklist
from schemas.auth import ForgotPasswordRequest, ResetPasswordRequest, Token, UserLogin, RefreshTokenRequest, SessionInfo
from schemas.user import UserCreate, UserInfoResponse, UserResponse
from utils.security import (
    get_password_hash, 
    verify_password, 
    create_access_token
)
from config import SECRET_KEY, ALGORITHM, REFRESH_TOKEN_EXPIRE_DAYS, ACCESS_TOKEN_EXPIRE_MINUTES
from services.email_service import email_service  # <- import our email service

router = APIRouter(prefix="/auth", tags=["authentication"])

def create_refresh_token(user_id: int, db: Session, device_info: str = None):
    jti = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode = {
        "sub": str(user_id),
        "jti": jti,
        "exp": expire,
        "type": "refresh"
    }
    
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    db_token = RefreshToken(
        jti=jti,
        user_id=user_id,
        token=token,
        expires_at=expire,
        device_info=device_info,
        is_active=True
    )
    db.add(db_token)
    db.commit()
    
    return token, jti

def blacklist_token(jti: str, token_type: str, user_id: int, expires_at: datetime, db: Session):
    blacklist_entry = TokenBlacklist(
        jti=jti,
        token_type=token_type,
        user_id=user_id,
        expires_at=expires_at
    )
    db.add(blacklist_entry)
    db.commit()

@router.post("/register")
async def register(
    request: Request,
    user: UserCreate,
    db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    hashed_password = get_password_hash(user.password)
    new_user = User(
        email=user.email,
        firstName=user.firstName,
        lastName=user.lastName,
        password_hash=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    role = db.query(Role).filter(Role.name == user.role).first()
    if not role:
        role = Role(name=user.role)
        db.add(role)
        db.commit()
        db.refresh(role)
    
    role_user = RoleUser(user_id=new_user.id, role_id=role.id)
    db.add(role_user)
    db.commit()
    
    return {"message": "User registered successfully", "user_id": new_user.id}

@router.post("/login", response_model=Token)
async def login(
    request: Request,
    user_login: UserLogin,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == user_login.email).first()
    
    if not user or not verify_password(user_login.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    access_token, access_jti, access_exp = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    refresh_token, refresh_jti = create_refresh_token(
        user.id,
        db,
        device_info=request.headers.get("User-Agent")
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )

@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_request: RefreshTokenRequest, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(refresh_request.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        user_id = int(payload.get("sub"))
        
        from dependencies import is_token_blacklisted
        if is_token_blacklisted(jti, db):
            raise HTTPException(status_code=401, detail="Token has been revoked")
        
        db_token = db.query(RefreshToken).filter(
            RefreshToken.jti == jti,
            RefreshToken.is_active == True
        ).first()
        
        if not db_token:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        db_token.is_active = False
        db.commit()
        
        blacklist_token(jti, "refresh", user_id, db_token.expires_at, db)
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        access_token, access_jti, access_exp = create_access_token(
            data={"sub": user.email},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        new_refresh_token, new_refresh_jti = create_refresh_token(user.id, db)
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    jti = payload.get("jti")
    exp = datetime.fromtimestamp(payload.get("exp"))
    
    blacklist_token(jti, "access", current_user.id, exp, db)
    
    active_tokens = db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id,
        RefreshToken.is_active == True
    ).all()
    
    for token in active_tokens:
        token.is_active = False
        blacklist_token(token.jti, "refresh", current_user.id, token.expires_at, db)
    
    db.commit()
    
    return {"message": "Logged out successfully"}

@router.post("/logout-all")
async def logout_all_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    active_tokens = db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id,
        RefreshToken.is_active == True
    ).all()
    
    for token in active_tokens:
        token.is_active = False
        blacklist_token(token.jti, "refresh", current_user.id, token.expires_at, db)
    
    db.commit()
    
    return {
        "message": f"Logged out from {len(active_tokens)} devices",
        "sessions_terminated": len(active_tokens)
    }

@router.get("/active-sessions", response_model=SessionInfo)
async def get_active_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    active_tokens = db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id,
        RefreshToken.is_active == True
    ).all()
    
    return {
        "active_sessions": len(active_tokens),
        "device_info": [t.device_info or "Unknown device" for t in active_tokens]
    }

@router.get("/me", response_model=UserInfoResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == current_user.id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    role_names = [role_user.role.name for role_user in user.roles]
    
    user_data = UserResponse(
        id=user.id,
        email=user.email,
        first_name=user.firstName,
        last_name=user.lastName,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        updated_at=user.updated_at,
        roles=role_names
    )
    
    return {"user": user_data}

@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == request.email).first()
    
    # Always return success message (security)
    message = {"message": "If that email exists, a reset link has been sent."}
    
    if not user:
        return message
    
    # Generate token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)
    
    reset_token = PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=expires_at
    )
    db.add(reset_token)
    db.commit()
    
    # Build reset link (adjust frontend URL)
    reset_link = f"http://localhost:3000/auth/reset-password?token={token}"
    
    # Send email
    try:
        await email_service.send_reset_password_email(user.email, reset_link)
    except Exception as e:
        print(f"Failed to send reset email: {e}")
    
    return message

@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    # Find token
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == request.token,
        PasswordResetToken.used == False
    ).first()
    
    if not reset_token:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    # Check if token expired
    if datetime.utcnow() > reset_token.expires_at:
        raise HTTPException(status_code=400, detail="Token has expired")
    
    # Get user
    user = db.query(User).filter(User.id == reset_token.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update password (hash it first!)
    user.password_hash = get_password_hash(request.new_password)


    # Mark token as used
    reset_token.used = True
    
    db.commit()
    
    return {"message": "Password reset successful"}

@router.get("/verify-reset-token/{token}")
async def verify_reset_token(
    token: str,
    db: Session = Depends(get_db)
):
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == token,
        PasswordResetToken.used == False
    ).first()
    
    if not reset_token or datetime.utcnow() > reset_token.expires_at:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    return {"valid": True}
