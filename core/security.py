// core/security.py
"""Security utilities for JWT and password handling."""

from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import settings

# Password hashing context using bcrypt
pwd_context: CryptContext = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)

# HTTP Bearer token security scheme
bearer_scheme = HTTPBearer(
    scheme_name="JWT Bearer Token",
    description="JWT token for API authentication",
    auto_error=True,
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash.

    Args:
        plain_password: Plain text password.
        hashed_password: Hashed password to verify against.

    Returns:
        True if password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: Plain text password to hash.

    Returns:
        Hashed password string.
    """
    return pwd_context.hash(password)


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token.

    Args:
        data: Data to encode in the token.
        expires_delta: Token expiration time delta.

    Returns:
        Encoded JWT token string.
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt_access_token_expire_minutes,
        )

    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT access token.

    Args:
        token: JWT token string.

    Returns:
        Decoded token payload.

    Raises:
        HTTPException: If token is invalid or expired.
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
            detail=f"Invalid or expired token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> str:
    """Extract user ID from JWT token.

    Args:
        credentials: HTTP Bearer credentials.

    Returns:
        User ID from token.

    Raises:
        HTTPException: If token is invalid or user_id not in payload.
    """
    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return str(user_id)


class TokenData:
    """Token data container."""

    def __init__(
        self,
        sub: str,
        exp: datetime,
        iat: datetime,
        **extra: Any,
    ) -> None:
        self.sub = sub
        self.exp = exp
        self.iat = iat
        for key, value in extra.items():
            setattr(self, key, value)

    @classmethod
    def from_token(cls, token: str) -> "TokenData":
        """Create TokenData from JWT token string.

        Args:
            token: JWT token string.

        Returns:
            TokenData instance.
        """
        payload = decode_access_token(token)
        return cls(**payload)

    def to_dict(self) -> dict[str, Any]:
        """Convert TokenData to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "sub": self.sub,
            "exp": self.exp,
            "iat": self.iat,
        }


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT refresh token.

    Args:
        data: Data to encode in the token.
        expires_delta: Token expiration time delta.

    Returns:
        Encoded JWT refresh token string.
    """
    to_encode = data.copy()
    to_encode["type"] = "refresh"

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)

    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    return encoded_jwt
