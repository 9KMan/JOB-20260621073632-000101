# core/security.py
"""JWT and password hashing utilities."""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import get_settings


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password.

    Args:
        plain_password: The plain text password
        hashed_password: The hashed password to verify against

    Returns:
        bool: True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: The plain text password to hash

    Returns:
        str: The hashed password
    """
    return pwd_context.hash(password)


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
    token_type: str = "access",
) -> str:
    """Create a JWT access token.

    Args:
        data: The payload data to encode in the token
        expires_delta: Optional custom expiration time
        token_type: Type of token (access or refresh)

    Returns:
        str: The encoded JWT token
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


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT access token.

    Args:
        token: The JWT token to decode

    Returns:
        dict | None: The decoded payload if valid, None otherwise
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError:
        return None


def verify_token(token: str, token_type: str = "access") -> dict[str, Any] | None:
    """Verify a JWT token and check its type.

    Args:
        token: The JWT token to verify
        token_type: Expected token type

    Returns:
        dict | None: The decoded payload if valid and type matches, None otherwise
    """
    payload = decode_access_token(token)
    if payload is None:
        return None

    if payload.get("type") != token_type:
        return None

    return payload


def create_refresh_token(data: dict[str, Any]) -> str:
    """Create a JWT refresh token.

    Args:
        data: The payload data to encode in the token

    Returns:
        str: The encoded JWT refresh token
    """
    return create_access_token(data, token_type="refresh")


class TokenData:
    """Token payload data structure."""

    def __init__(
        self,
        subject: str,
        user_id: str | None = None,
        email: str | None = None,
        roles: list[str] | None = None,
    ):
        self.subject = subject
        self.user_id = user_id
        self.email = email
        self.roles = roles or []

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "TokenData":
        """Create TokenData from JWT payload."""
        return cls(
            subject=payload.get("sub", ""),
            user_id=payload.get("user_id"),
            email=payload.get("email"),
            roles=payload.get("roles", []),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JWT encoding."""
        return {
            "sub": self.subject,
            "user_id": self.user_id,
            "email": self.email,
            "roles": self.roles,
        }
