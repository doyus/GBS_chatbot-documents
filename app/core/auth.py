import jwt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer(auto_error=False)


class UserRegister(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    username_or_email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: Dict[str, Any]


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: str
    last_login: Optional[str] = None


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user_from_token(token: str) -> Dict[str, Any]:
    payload = decode_token(token)
    user_id = payload.get("sub")
    username = payload.get("username")
    
    if user_id is None or username is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    return {
        "user_id": user_id,
        "username": username,
        "email": payload.get("email")
    }


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    token = credentials.credentials
    return get_current_user_from_token(token)


async def get_optional_user(request: Request) -> Optional[Dict[str, Any]]:
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
    
    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            return None
        return get_current_user_from_token(token)
    except (ValueError, HTTPException):
        return None


def verify_password_strength(password: str) -> tuple:
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    
    has_letter = any(c.isalpha() for c in password)
    has_number = any(c.isdigit() for c in password)
    
    if not has_letter or not has_number:
        return False, "Password must contain both letters and numbers"
    
    return True, "Password is strong"


def validate_email(email: str) -> bool:
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None
