# core/security.py
"""Security utilities for JWT and password management.

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
    """Verify a plain password against a hashed password.

    Args:
        plain_password: The plain text password to verify
        hashed_password: The hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: The plain text password to hash

    Returns:
        The bcrypt hashed password
    """
    return pwd_context.hash(password)


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
    token_type: str = "access",
) -> str:
    """Create a JWT access token.

    Args:
        data: Payload data to encode in the token
        expires_delta: Optional custom expiration time
        token_type: Type of token (access or refresh)

    Returns:
        Encoded JWT token string
    """
    settings = get_settings()

    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        if token_type == "refresh":
            expire = datetime.now(timezone.utc) + timedelta(
                days=settings.jwt_refresh_token_expire_days
            )
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.jwt_access_token_expire_minutes
            )

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": token_type,
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    return encoded_jwt


def create_refresh_token(user_id: str) -> str:
    """Create a JWT refresh token.

    Args:
        user_id: User identifier for the token

    Returns:
        Encoded JWT refresh token string
    """
    return create_access_token(
        data={"sub": user_id, "token_type": "refresh"},
        token_type="refresh",
    )


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT token.

    Args:
        token: JWT token string to decode

    Returns:
        Decoded token payload or None if invalid
    """
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        return None


def verify_access_token(token: str) -> dict[str, Any] | None:
    """Verify an access token and return its payload.

    Args:
        token: JWT access token string

    Returns:
        Token payload if valid, None otherwise
    """
    payload = decode_token(token)

    if payload is None:
        return None

    if payload.get("type") != "access":
        logger.warning("Token type mismatch - expected access token")
        return None

    return payload


def get_token_expiration(token: str) -> datetime | None:
    """Get the expiration datetime from a token.

    Args:
        token: JWT token string

    Returns:
        Expiration datetime or None if invalid
    """
    payload = decode_token(token)

    if payload is None:
        return None

    exp = payload.get("exp")

    if exp is None:
        return None

    return datetime.fromtimestamp(exp, tz=timezone.utc)
