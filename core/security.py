// core/security.py
"""JWT and password hashing utilities.

Provides secure authentication helpers using bcrypt for password
hashing and HS256 JWT tokens for authentication.
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ValidationError

from core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Bearer scheme
bearer_scheme = HTTPBearer(auto_error=False)


class TokenData(BaseModel):
    """Decoded JWT token data."""

    sub: str | None = None
    exp: datetime | None = None
    iat: datetime | None = None


class TokenPayload(BaseModel):
    """JWT token payload for encoding."""

    sub: str
    exp: datetime | None = None
    iat: datetime | None = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.

    Args:
        plain_password: Plain text password.
        hashed_password: Bcrypt hashed password.

    Returns:
        True if password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: Plain text password to hash.

    Returns:
        Bcrypt hashed password string.
    """
    return pwd_context.hash(password)


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
    additional_claims: dict | None = None,
) -> str:
    """Create a JWT access token.

    Args:
        subject: Token subject (usually user ID).
        expires_delta: Optional custom expiration time.
        additional_claims: Optional additional JWT claims.

    Returns:
        Encoded JWT token string.
    """
    now = datetime.now(timezone.utc)
    
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)

    payload = {
        "sub": subject,
        "exp": expire,
        "iat": now,
    }
    
    if additional_claims:
        payload.update(additional_claims)

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> TokenData | None:
    """Decode and validate a JWT token.

    Args:
        token: JWT token string to decode.

    Returns:
        TokenData if valid, None if invalid.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return TokenData(**payload)
    except JWTError:
        return None


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> str | None:
    """Extract user ID from JWT token.

    Args:
        credentials: HTTP Bearer credentials from request.

    Returns:
        User ID from token subject, or None if invalid.
    """
    if credentials is None:
        return None

    token_data = decode_token(credentials.credentials)
    
    if token_data is None or token_data.sub is None:
        return None

    # Check expiration
    if token_data.exp and token_data.exp < datetime.now(timezone.utc):
        return None

    return token_data.sub


async def require_auth(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer())],
) -> str:
    """Require valid authentication - raises 401 if invalid.

    Args:
        credentials: Required HTTP Bearer credentials.

    Returns:
        User ID from validated token.

    Raises:
        HTTPException: 401 if token is invalid or missing.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = decode_token(credentials.credentials)
    
    if token_data is None or token_data.sub is None:
        raise credentials_exception

    # Check expiration
    if token_data.exp and token_data.exp < datetime.now(timezone.utc):
        raise credentials_exception

    return token_data.sub
