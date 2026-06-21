# core/security.py
"""Security utilities for JWT and password hashing.

Provides:
- JWT token creation and validation
- Password hashing and verification
- Current user extraction from tokens
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import settings


# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password.

    Args:
        plain_password: The plain text password to verify.
        hashed_password: The bcrypt hashed password.

    Returns:
        bool: True if password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: The plain text password to hash.

    Returns:
        str: The bcrypt hashed password.
    """
    return pwd_context.hash(password)


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token.

    Args:
        data: The payload data to encode in the token.
        expires_delta: Optional custom expiration time.

    Returns:
        str: The encoded JWT token.
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
        expires_delta: Optional custom expiration time.

    Returns:
        str: The encoded JWT refresh token.
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


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT token.

    Args:
        token: The JWT token to decode.

    Returns:
        dict | None: The decoded payload if valid, None otherwise.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError:
        return None


def verify_token(token: str, expected_type: str = "access") -> dict[str, Any] | None:
    """Verify a JWT token and check its type.

    Args:
        token: The JWT token to verify.
        expected_type: Expected token type ('access' or 'refresh').

    Returns:
        dict | None: The decoded payload if valid, None otherwise.
    """
    payload = decode_token(token)
    if payload is None:
        return None

    if payload.get("type") != expected_type:
        return None

    return payload


class TokenPayload:
    """Token payload with type-safe accessors."""

    def __init__(self, payload: dict[str, Any]):
        self._payload = payload

    @property
    def sub(self) -> str | None:
        """Subject (usually user ID)."""
        return self._payload.get("sub")

    @property
    def exp(self) -> datetime | None:
        """Expiration time."""
        exp = self._payload.get("exp")
        if exp:
            return datetime.fromtimestamp(exp, tz=timezone.utc)
        return None

    @property
    def iat(self) -> datetime | None:
        """Issued at time."""
        iat = self._payload.get("iat")
        if iat:
            return datetime.fromtimestamp(iat, tz=timezone.utc)
        return None

    @property
    def token_type(self) -> str:
        """Token type."""
        return self._payload.get("type", "unknown")

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        if self.exp is None:
            return False
        return datetime.now(timezone.utc) > self.exp

    @property
    def user_id(self) -> str | None:
        """Get user ID from subject."""
        return self.sub

    @property
    def role(self) -> str | None:
        """Get user role from token."""
        return self._payload.get("role")

    def get(self, key: str, default: Any = None) -> Any:
        """Get arbitrary claim from token."""
        return self._payload.get(key, default)
