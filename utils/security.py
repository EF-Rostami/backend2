from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
import uuid
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS

pwd_context = CryptContext(
    schemes=["argon2"],
    default="argon2",
    deprecated="auto"
)

def validate_password_strength(password: str) -> bool:
    """
    Validate password meets minimum security requirements:
    - At least 8 characters
    - Contains uppercase and lowercase
    - Contains at least one digit
    - Contains at least one special character
    """
    if len(password) < 8:
        return False
    if not any(c.isupper() for c in password):
        return False
    if not any(c.islower() for c in password):
        return False
    if not any(c.isdigit() for c in password):
        return False
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False
    return True

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> Tuple[str, str, datetime]:
    to_encode = data.copy()
    jti = str(uuid.uuid4())
    to_encode.update({
        "jti": jti,
        "type": "access"
    })
    
    if expires_delta:
        
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, jti, expire

def generate_password(first_name: str, date_of_birth) -> str:
    """
    Generate password: first3letters + ddmmyyyy
    Handles edge cases
    """
    # Clean the name
    clean_name = ''.join(c for c in first_name if c.isalpha())
    
    if len(clean_name) < 3:
        clean_name = clean_name.ljust(3, 'x')  # Pad if too short
    
    name_part = clean_name[:3].lower()
    
    day = str(date_of_birth.day).zfill(2)
    month = str(date_of_birth.month).zfill(2)
    year = str(date_of_birth.year)
    
    return f"{name_part}{day}{month}{year}"