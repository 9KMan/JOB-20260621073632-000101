// core/security.py
"""Security utilities for JWT authentication and password hashing.

Provides:
- JWT token creation and validation (HS256)
- Password hashing and verification using bcrypt
- Authentication dependencies for FastAPI
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ValidationError

from core.config import settings

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token security scheme
security = HTTPBearer()


class TokenData(BaseModel):
    """Token payload data."""

    sub: str | None = None
    exp: datetime | None = None
    iat: datetime | None = None
    token_type: str = "access"


class TokenResponse(BaseModel):
    """Token response model."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserBase(BaseModel):
    """Base user model."""

    username: str
    email: str | None = None
    is_active: bool = True


class UserInDB(UserBase):
    """User model with hashed password."""

    hashed_password: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.

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
    subject: str,
    expires_delta: timedelta | None = None,
    additional_claims: dict | None = None,
) -> str:
    """Create a JWT access token.

    Args:
        subject: The token subject (usually user identifier)
        expires_delta: Optional custom expiration time
        additional_claims: Additional claims to include in token

    Returns:
        str: Encoded JWT token
    """
    now = datetime.now(timezone.utc)

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)

    to_encode: dict = {
        "sub": subject,
        "exp": expire,
        "iat": now,
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


def decode_token(token: str) -> TokenData:
    """Decode and validate a JWT token.

    Args:
        token: The JWT token to decode

    Returns:
        TokenData: Decoded token data

    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        subject: str | None = payload.get("sub")
        token_type: str | None = payload.get("type")

        if subject is None:
            raise credentials_exception

        if token_type != "access":
            raise credentials_exception

        return TokenData(
            sub=subject,
            exp=datetime.fromtimestamp(payload.get("exp"), tz=timezone.utc),
            iat=datetime.fromtimestamp(payload.get("iat"), tz=timezone.utc),
            token_type=token_type,
        )
    except JWTError:
        raise credentials_exception
    except ValidationError:
        raise credentials_exception


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> str:
    """Get current user from JWT token.

    This is a FastAPI dependency that extracts and validates
    the user identity from the JWT token.

    Args:
        credentials: HTTP Bearer credentials

    Returns:
        str: The user identifier (subject)

    Raises:
        HTTPException: If token is invalid
    """
    token_data = decode_token(credentials.credentials)
    return token_data.sub


# Type alias for dependency injection
CurrentUser = Annotated[str, Depends(get_current_user)]
