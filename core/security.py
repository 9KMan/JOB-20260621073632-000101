# core/security.py
"""JWT and password hashing utilities using HS256 and bcrypt."""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import settings

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash.

    Args:
        plain_password: The plain-text password.
        hashed_password: The bcrypt-hashed password.

    Returns:
        True if the password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: The plain-text password to hash.

    Returns:
        The bcrypt hash string.
    """
    return pwd_context.hash(password)


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token using HS256.

    Args:
        data: Payload data to encode in the token.
        expires_delta: Optional custom expiry timedelta.

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(minutes=settings.jwt.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(
        to_encode,
        settings.jwt.secret_key,
        algorithm=settings.jwt.algorithm,
    )


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT access token.

    Args:
        token: The JWT string to decode.

    Returns:
        Decoded payload dict, or None if invalid/expired.
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
