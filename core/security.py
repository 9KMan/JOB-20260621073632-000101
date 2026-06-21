# core/security.py
"""Security utilities for JWT and password hashing."""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import settings

# Password hashing context using bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def create_access_token(
    subject: str | Any,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a JWT access token.

    Args:
        subject: The token subject (usually user ID)
        expires_delta: Optional custom expiration time
        extra_claims: Additional claims to include in the token

    Returns:
        Encoded JWT token string
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt.jwt_access_token_expire_minutes
        )

    to_encode: dict[str, Any] = {
        "exp": expire,
        "sub": str(subject),
        "type": "access",
    }

    if extra_claims:
        to_encode.update(extra_claims)

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt.jwt_secret_key,
        algorithm=settings.jwt.jwt_algorithm,
    )
    return encoded_jwt


def create_refresh_token(
    subject: str | Any,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT refresh token.

    Args:
        subject: The token subject (usually user ID)
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT refresh token string
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.jwt.jwt_refresh_token_expire_days
        )

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt.jwt_secret_key,
        algorithm=settings.jwt.jwt_algorithm,
    )
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT token.

    Args:
        token: The JWT token string

    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt.jwt_secret_key,
            algorithms=[settings.jwt.jwt_algorithm],
        )
        return payload
    except JWTError:
        return None


def verify_access_token(token: str) -> str | None:
    """Verify an access token and return the subject.

    Args:
        token: The JWT access token string

    Returns:
        Subject (user ID) if valid, None otherwise
    """
    payload = decode_token(token)
    if payload is None:
        return None

    token_type = payload.get("type")
    if token_type != "access":
        return None

    return payload.get("sub")


__all__ = [
    "pwd_context",
    "verify_password",
    "hash_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "verify_access_token",
]
