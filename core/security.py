# core/security.py
"""Security utilities for authentication and authorization.

Provides JWT token handling and password hashing using bcrypt.
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import settings


# Password hashing context using bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.security.bcrypt_rounds,
)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: Plain text password to hash.

    Returns:
        str: Bcrypt hashed password.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash.

    Args:
        plain_password: Plain text password to verify.
        hashed_password: Bcrypt hashed password.

    Returns:
        bool: True if password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token.

    Args:
        data: Payload data to encode in the token.
        expires_delta: Optional expiration time delta.

    Returns:
        str: Encoded JWT token.
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.security.jwt_access_token_expire_minutes
        )

    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.security.jwt_secret_key,
        algorithm=settings.security.jwt_algorithm,
    )

    return encoded_jwt


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT refresh token.

    Args:
        data: Payload data to encode in the token.
        expires_delta: Optional expiration time delta.

    Returns:
        str: Encoded JWT refresh token.
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.security.jwt_refresh_token_expire_days
        )

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.security.jwt_secret_key,
        algorithm=settings.security.jwt_algorithm,
    )

    return encoded_jwt


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT token.

    Args:
        token: JWT token string to decode.

    Returns:
        dict | None: Decoded token payload or None if invalid.
    """
    try:
        payload = jwt.decode(
            token,
            settings.security.jwt_secret_key,
            algorithms=[settings.security.jwt_algorithm],
        )
        return payload
    except JWTError:
        return None


def verify_token(token: str) -> bool:
    """Verify if a JWT token is valid.

    Args:
        token: JWT token string to verify.

    Returns:
        bool: True if token is valid, False otherwise.
    """
    return decode_token(token) is not None


class TokenPayload:
    """JWT token payload model."""

    def __init__(
        self,
        sub: str,
        exp: datetime,
        iat: datetime,
        type: str = "access",
    ) -> None:
        self.sub = sub
        self.exp = exp
        self.iat = iat
        self.type = type

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TokenPayload":
        """Create TokenPayload from decoded token dictionary."""
        return cls(
            sub=data.get("sub", ""),
            exp=datetime.fromtimestamp(data.get("exp", 0), tz=timezone.utc),
            iat=datetime.fromtimestamp(data.get("iat", 0), tz=timezone.utc),
            type=data.get("type", "access"),
        )


__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "verify_token",
    "TokenPayload",
]
