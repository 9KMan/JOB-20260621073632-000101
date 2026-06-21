# core/security.py
"""Security utilities for JWT authentication and password hashing."""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from core.config import get_settings


# Password hashing context using bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)


class TokenPayload(BaseModel):
    """JWT token payload model."""

    sub: str  # Subject (user ID or identifier)
    exp: datetime  # Expiration time
    iat: datetime  # Issued at time
    type: str = "access"  # Token type (access or refresh)
    extra: dict[str, Any] | None = None


class TokenPair(BaseModel):
    """Access and refresh token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
    extra: dict[str, Any] | None = None,
) -> str:
    """Create a JWT access token.

    Args:
        subject: The token subject (typically user ID).
        expires_delta: Optional custom expiration time.
        extra: Optional extra claims to include.

    Returns:
        The encoded JWT token string.
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

    if extra:
        to_encode["extra"] = extra

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt.secret_key,
        algorithm=settings.jwt.algorithm,
    )
    return encoded_jwt


def create_refresh_token(
    subject: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT refresh token.

    Args:
        subject: The token subject (typically user ID).
        expires_delta: Optional custom expiration time.

    Returns:
        The encoded JWT refresh token string.
    """
    settings = get_settings()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.jwt.refresh_token_expire_days
        )

    to_encode: dict[str, Any] = {
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


def create_token_pair(
    subject: str,
    extra: dict[str, Any] | None = None,
) -> TokenPair:
    """Create an access/refresh token pair.

    Args:
        subject: The token subject (typically user ID).
        extra: Optional extra claims for access token.

    Returns:
        A TokenPair containing both tokens.
    """
    access_token = create_access_token(subject, extra=extra)
    refresh_token = create_refresh_token(subject)

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
    )


def decode_token(token: str) -> TokenPayload | None:
    """Decode and validate a JWT token.

    Args:
        token: The JWT token string.

    Returns:
        The decoded TokenPayload if valid, None otherwise.
    """
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.jwt.secret_key,
            algorithms=[settings.jwt.algorithm],
        )

        return TokenPayload(
            sub=payload.get("sub", ""),
            exp=datetime.fromtimestamp(payload.get("exp", 0), tz=timezone.utc),
            iat=datetime.fromtimestamp(payload.get("iat", 0), tz=timezone.utc),
            type=payload.get("type", "access"),
            extra=payload.get("extra"),
        )
    except JWTError:
        return None


def verify_token(token: str) -> bool:
    """Verify if a token is valid.

    Args:
        token: The JWT token string.

    Returns:
        True if valid, False otherwise.
    """
    payload = decode_token(token)
    if not payload:
        return False

    # Check expiration
    if payload.exp < datetime.now(timezone.utc):
        return False

    return True


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: The plaintext password.

    Returns:
        The bcrypt hash of the password.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.

    Args:
        plain_password: The plaintext password to verify.
        hashed_password: The bcrypt hash to verify against.

    Returns:
        True if the password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


async def get_current_user(token: str) -> str | None:
    """Get the current user ID from a token.

    This is an async function to match FastAPI dependency injection pattern.
    For actual user lookup, implement your user repository.

    Args:
        token: The JWT token string.

    Returns:
        The user ID (subject) if valid, None otherwise.
    """
    payload = decode_token(token)

    if not payload:
        return None

    if payload.exp < datetime.now(timezone.utc):
        return None

    return payload.sub


class AuthenticationError(Exception):
    """Custom authentication error."""

    pass


def require_authentication(token: str) -> str:
    """Require a valid authentication token.

    Args:
        token: The JWT token string.

    Returns:
        The user ID (subject).

    Raises:
        AuthenticationError: If the token is invalid or expired.
    """
    user_id = get_current_user(token)

    if not user_id:
        raise AuthenticationError("Invalid or expired token")

    return user_id
