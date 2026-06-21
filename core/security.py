# core/security.py
"""
Security utilities for JWT authentication and password hashing.

Provides JWT token creation/validation and password hashing
using bcrypt via passlib.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import get_settings

logger = logging.getLogger(__name__)

# Password hashing context using bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: The plain text password to verify.
        hashed_password: The hashed password to compare against.
    
    Returns:
        bool: True if password matches, False otherwise.
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.warning(f"Password verification failed: {e}")
        return False


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: The plain text password to hash.
    
    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)


def create_access_token(
    subject: str | Any,
    expires_delta: timedelta | None = None,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    """
    Create a JWT access token.
    
    Args:
        subject: The token subject (typically user ID).
        expires_delta: Optional custom expiration time.
        additional_claims: Optional additional claims to include.
    
    Returns:
        str: The encoded JWT token.
    """
    settings = get_settings()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt.access_token_expire_minutes
        )
    
    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    
    if additional_claims:
        to_encode.update(additional_claims)
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt.secret_key,
        algorithm=settings.jwt.algorithm,
    )
    
    return encoded_jwt


def create_refresh_token(
    subject: str | Any,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        subject: The token subject (typically user ID).
        expires_delta: Optional custom expiration time.
    
    Returns:
        str: The encoded JWT refresh token.
    """
    settings = get_settings()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.jwt.refresh_token_expire_days
        )
    
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt.secret_key,
        algorithm=settings.jwt.algorithm,
    )
    
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any] | None:
    """
    Decode and validate a JWT token.
    
    Args:
        token: The JWT token to decode.
    
    Returns:
        dict | None: The decoded token payload, or None if invalid.
    """
    settings = get_settings()
    
    try:
        payload = jwt.decode(
            token,
            settings.jwt.secret_key,
            algorithms=[settings.jwt.algorithm],
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        return None


def verify_token(
    token: str,
    expected_type: str = "access",
) -> str | None:
    """
    Verify a token and return the subject if valid.
    
    Args:
        token: The JWT token to verify.
        expected_type: The expected token type ('access' or 'refresh').
    
    Returns:
        str | None: The token subject if valid, None otherwise.
    """
    payload = decode_token(token)
    
    if payload is None:
        return None
    
    # Verify token type
    token_type = payload.get("type")
    if token_type != expected_type:
        logger.warning(f"Invalid token type: expected {expected_type}, got {token_type}")
        return None
    
    # Get and verify expiration
    exp = payload.get("exp")
    if exp:
        exp_datetime = datetime.fromtimestamp(exp, tz=timezone.utc)
        if datetime.now(timezone.utc) > exp_datetime:
            logger.warning("Token has expired")
            return None
    
    return payload.get("sub")


def create_password_reset_token(subject: str) -> str:
    """
    Create a password reset token with a short expiration.
    
    Args:
        subject: The user identifier.
    
    Returns:
        str: The encoded JWT token.
    """
    settings = get_settings()
    
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "password_reset",
    }
    
    return jwt.encode(
        to_encode,
        settings.jwt.secret_key,
        algorithm=settings.jwt.algorithm,
    )


def verify_password_reset_token(token: str) -> str | None:
    """
    Verify a password reset token.
    
    Args:
        token: The password reset token.
    
    Returns:
        str | None: The subject if valid, None otherwise.
    """
    payload = decode_token(token)
    
    if payload is None:
        return None
    
    if payload.get("type") != "password_reset":
        return None
    
    return payload.get("sub")
