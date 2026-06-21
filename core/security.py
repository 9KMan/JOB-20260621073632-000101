// core/security.py
"""Security utilities for authentication and authorization."""
from datetime import datetime, timedelta, timezone
from typing import Optional, Any

from jose import jwt, JWTError
from passlib.context import CryptContext

from core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[dict] = None,
) -> str:
    """
    Create a JWT access token.
    
    Args:
        subject: The token subject (usually user ID)
        expires_delta: Optional custom expiration time
        additional_claims: Optional additional claims to include
        
    Returns:
        Encoded JWT token string
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt_expiration_minutes
        )
    
    to_encode: dict[str, Any] = {
        "exp": expire,
        "sub": str(subject),
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    
    if additional_claims:
        to_encode.update(additional_claims)
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    """
    Decode and verify a JWT access token.
    
    Args:
        token: The JWT token string
        
    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError:
        return None


def verify_token(token: str) -> Optional[str]:
    """
    Verify a token and return the subject (user ID).
    
    Args:
        token: The JWT token string
        
    Returns:
        User ID from token or None if invalid
    """
    payload = decode_access_token(token)
    if payload is None:
        return None
    
    token_type = payload.get("type")
    if token_type != "access":
        return None
    
    return payload.get("sub")
