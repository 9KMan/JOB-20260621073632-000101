# core/security.py
"""Security utilities for JWT authentication and password hashing."""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import settings


# Password hashing context using bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.bcrypt_rounds,
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password.

    Args:
        plain_password: The plain text password to verify.
        hashed_password: The hashed password to compare against.

    Returns:
        True if the password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: The plain text password to hash.

    Returns:
        The hashed password string.
    """
    return pwd_context.hash(password)


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token.

    Args:
        data: The payload data to encode in the token.
        expires_delta: Optional custom expiration time delta.

    Returns:
        The encoded JWT token string.
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    return encoded_jwt


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT refresh token.

    Args:
        data: The payload data to encode in the token.
        expires_delta: Optional custom expiration time delta.

    Returns:
        The encoded JWT refresh token string.
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.jwt_refresh_token_expire_days
        )

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    return encoded_jwt


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token.

    Args:
        token: The JWT token string to decode.

    Returns:
        The decoded token payload.

    Raises:
        JWTError: If the token is invalid or expired.
    """
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )


def verify_access_token(token: str) -> dict[str, Any]:
    """Verify an access token and return its payload.

    Args:
        token: The JWT access token to verify.

    Returns:
        The decoded token payload.

    Raises:
        JWTError: If the token is invalid or not an access token.
    """
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise JWTError("Invalid token type, expected access token")
    return payload


def verify_refresh_token(token: str) -> dict[str, Any]:
    """Verify a refresh token and return its payload.

    Args:
        token: The JWT refresh token to verify.

    Returns:
        The decoded token payload.

    Raises:
        JWTError: If the token is invalid or not a refresh token.
    """
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise JWTError("Invalid token type, expected refresh token")
    return payload
