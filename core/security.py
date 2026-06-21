// core/security.py
"""Security utilities for JWT and password handling.

This module provides authentication and authorization utilities
using HS256 JWT tokens and bcrypt password hashing.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import settings


# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password.

    Args:
        plain_password: The plain text password to verify.
        hashed_password: The hashed password to compare against.

    Returns:
        bool: True if passwords match, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: The plain text password to hash.

    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)


def create_access_token(
    data: dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token.

    Args:
        data: The payload data to encode in the token.
        expires_delta: Optional expiration time delta.

    Returns:
        str: The encoded JWT token.
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt.access_token_expire_minutes
        )

    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt.secret_key,
        algorithm=settings.jwt.algorithm,
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    """Decode and validate a JWT access token.

    Args:
        token: The JWT token to decode.

    Returns:
        Optional[dict]: The decoded payload if valid, None otherwise.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt.secret_key,
            algorithms=[settings.jwt.algorithm],
        )
        return payload
    except JWTError:
        return None


def verify_token(token: str) -> bool:
    """Verify if a JWT token is valid.

    Args:
        token: The JWT token to verify.

    Returns:
        bool: True if token is valid, False otherwise.
    """
    payload = decode_access_token(token)
    return payload is not None


class TokenData:
    """Token payload data class."""

    def __init__(
        self,
        sub: str,
        exp: datetime,
        iat: datetime,
        role: Optional[str] = None,
    ):
        self.sub = sub
        self.exp = exp
        self.iat = iat
        self.role = role

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "TokenData":
        """Create TokenData from JWT payload.

        Args:
            payload: The decoded JWT payload.

        Returns:
            TokenData: The token data instance.
        """
        return cls(
            sub=payload.get("sub", ""),
            exp=datetime.fromtimestamp(payload.get("exp", 0), tz=timezone.utc),
            iat=datetime.fromtimestamp(payload.get("iat", 0), tz=timezone.utc),
            role=payload.get("role"),
        )
