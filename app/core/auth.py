import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
import json

SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_hex(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256((password + salt).encode())
    return f"{salt}${hash_obj.hexdigest()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        salt, stored_hash = hashed_password.split('$')
        hash_obj = hashlib.sha256((plain_password + salt).encode())
        return hash_obj.hexdigest() == stored_hash
    except ValueError:
        return False

def base64url_encode(data: bytes) -> str:
    import base64
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def base64url_decode(data: str) -> bytes:
    import base64
    padding = 4 - len(data) % 4
    if padding != 4:
        data += '=' * padding
    return base64.urlsafe_b64decode(data)

def create_jwt_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire.timestamp()})
    
    header = {"alg": ALGORITHM, "typ": "JWT"}
    header_encoded = base64url_encode(json.dumps(header).encode())
    payload_encoded = base64url_encode(json.dumps(to_encode).encode())
    
    import hmac
    signature = hmac.new(
        SECRET_KEY.encode(),
        f"{header_encoded}.{payload_encoded}".encode(),
        hashlib.sha256
    ).digest()
    signature_encoded = base64url_encode(signature)
    
    return f"{header_encoded}.{payload_encoded}.{signature_encoded}"

def decode_jwt_token(token: str) -> Optional[dict]:
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        header_encoded, payload_encoded, signature_encoded = parts
        
        import hmac
        expected_signature = hmac.new(
            SECRET_KEY.encode(),
            f"{header_encoded}.{payload_encoded}".encode(),
            hashlib.sha256
        ).digest()
        expected_signature_encoded = base64url_encode(expected_signature)
        
        if signature_encoded != expected_signature_encoded:
            return None
        
        payload = json.loads(base64url_decode(payload_encoded).decode())
        
        if payload.get("exp", 0) < datetime.utcnow().timestamp():
            return None
        
        return payload
    except Exception:
        return None

def create_access_token(user_id: int, username: str) -> str:
    return create_jwt_token(
        data={"sub": username, "user_id": user_id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

def verify_token(token: str) -> Optional[dict]:
    return decode_jwt_token(token)
