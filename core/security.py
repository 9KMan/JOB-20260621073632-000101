// core/security.py
"""JWT and password hashing security utilities.

Provides JWT token creation/verification and password hashing
using bcrypt.
"""

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
        plain_password: Plain text password.
        hashed_password: Hashed password from database.

    Returns:
        bool: True if password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: Plain text password to hash.

    Returns:
        str: Hashed password.
    """
    return pwd_context.hash(password)


def create_access_token(
    subject: str | Any,
    expires_delta: timedelta | None = None,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    """Create a JWT access token.

    Args:
        subject: The token subject (typically user ID).
        expires_delta: Optional custom expiration time.
        additional_claims: Additional claims to include in token.

    Returns:
        str: Encoded JWT token.
    """
    settings = get_settings()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt.access_token_expire_minutes
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
        settings.jwt.secret_key,
        algorithm=settings.jwt.algorithm,
    )

    return encoded_jwt


def decode_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT token.

    Args:
        token: JWT token string.

    Returns:
        dict: Decoded token payload.

    Raises:
        JWTError: If token is invalid or expired.
    """
    settings = get_settings()

    payload = jwt.decode(
        token,
        settings.jwt.secret_key,
        algorithms=[settings.jwt.algorithm],
    )

    return payload


class TokenPayload:
    """JWT token payload model."""

    def __init__(
        self,
        exp: datetime,
        sub: str,
        iat: datetime,
        type: str,
        **extra: Any,
    ) -> None:
        self.exp = exp
        self.sub = sub
        self.iat = iat
        self.type = type
        self.extra = extra

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TokenPayload":
        """Create from decoded token dictionary."""
        return cls(
            exp=datetime.fromtimestamp(data["exp"], tz=timezone.utc),
            sub=data["sub"],
            iat=datetime.fromtimestamp(data["iat"], tz=timezone.utc),
            type=data.get("type", "access"),
            **{k: v for k, v in data.items() if k not in ("exp", "sub", "iat", "type")},
        )


class UserPayload:
    """User payload extracted from JWT token."""

    def __init__(
        self,
        user_id: str,
        email: str | None = None,
        roles: list[str] | None = None,
        **extra: Any,
    ) -> None:
        self.user_id = user_id
        self.email = email
        self.roles = roles or []
        self.extra = extra

    @classmethod
    def from_token_payload(cls, payload: dict[str, Any]) -> "UserPayload":
        """Create user payload from decoded JWT."""
        return cls(
            user_id=payload["sub"],
            email=payload.get("email"),
            roles=payload.get("roles", []),
            **{k: v for k, v in payload.items() if k not in ("sub", "email", "roles")},
        )


async def get_current_user(token: str) -> UserPayload:
    """Get current user from JWT token.

    This is an async wrapper for use in FastAPI dependencies.

    Args:
        token: JWT token string.

    Returns:
        UserPayload: Current user information.

    Raises:
        JWTError: If token is invalid or expired.
    """
    try:
        payload = decode_token(token)
        return UserPayload.from_token_payload(payload)
    except JWTError as e:
        raise JWTError(f"Invalid token: {e!s}") from e
