# core/security.py
"""Security utilities for JWT authentication and password hashing.

Provides JWT token creation/validation and password hashing using bcrypt.
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import settings

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token security scheme
bearer_scheme = HTTPBearer(auto_error=True)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Bcrypt hashed password

    Returns:
        bool: True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: Plain text password to hash

    Returns:
        str: Bcrypt hashed password
    """
    return pwd_context.hash(password)


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token.

    Args:
        data: Payload data to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )

    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    return encoded_jwt


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token.

    Args:
        token: JWT token string to decode

    Returns:
        dict: Decoded token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
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


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> str:
    """Dependency to get current user ID from JWT token.

    Args:
        credentials: HTTP Bearer credentials

    Returns:
        str: User ID from token payload

    Raises:
        HTTPException: If token is invalid or user_id not in payload
    """
    payload = decode_token(credentials.credentials)

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user identifier",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id


class TokenData:
    """Token payload data structure."""

    def __init__(
        self,
        sub: str,
        exp: datetime,
        iat: datetime,
        token_type: str = "access",
    ):
        self.sub = sub
        self.exp = exp
        self.iat = iat
        self.token_type = token_type
