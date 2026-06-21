// core/security.py
"""Security utilities for JWT authentication and password hashing."""

from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import get_settings

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme
bearer_scheme = HTTPBearer(auto_error=False)


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
        The bcrypt hashed password.
    """
    return pwd_context.hash(password)


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    """Create a JWT access token.

    Args:
        subject: The token subject (typically user ID or email).
        expires_delta: Optional custom expiration time delta.
        additional_claims: Optional additional JWT claims.

    Returns:
        The encoded JWT token string.
    """
    settings = get_settings()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }

    if additional_claims:
        to_encode.update(additional_claims)

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt


def create_refresh_token(
    subject: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT refresh token.

    Args:
        subject: The token subject (typically user ID or email).
        expires_delta: Optional custom expiration time delta.

    Returns:
        The encoded JWT refresh token string.
    """
    settings = get_settings()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.refresh_token_expire_days
        )

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT token.

    Args:
        token: The JWT token string to decode.

    Returns:
        The decoded token payload.

    Raises:
        HTTPException: If the token is invalid or expired.
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_access_token(token: str) -> dict[str, Any]:
    """Verify an access token and return its payload.

    Args:
        token: The JWT access token string.

    Returns:
        The decoded token payload.

    Raises:
        HTTPException: If the token is invalid, expired, or not an access token.
    """
    payload = decode_token(token)

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type: expected access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> str:
    """Extract and validate the current user ID from the JWT token.

    This is a FastAPI dependency for protecting endpoints.

    Args:
        credentials: The HTTP Bearer credentials.

    Returns:
        The user ID from the token.

    Raises:
        HTTPException: If authentication fails.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_access_token(credentials.credentials)
    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: missing subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id


# Type alias for dependency injection
CurrentUserId = Annotated[str, Depends(get_current_user_id)]
