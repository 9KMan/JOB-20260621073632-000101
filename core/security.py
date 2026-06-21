# core/security.py
"""Security utilities for JWT and password hashing.

Provides HS256 JWT token handling and bcrypt password hashing.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import get_settings


# Password hashing context using bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

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
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
    token_type: str = "access",
) -> str:
    """Create a JWT access token.

    Args:
        data: Payload data to encode in the token
        expires_delta: Optional custom expiration time
        token_type: Type of token (access or refresh)

    Returns:
        str: Encoded JWT token
    """
    settings = get_settings()
    jwt_settings = settings.jwt

    to_encode = data.copy()

    if token_type == "access":
        expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(minutes=jwt_settings.jwt_access_token_expire_minutes)
        )
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=jwt_settings.jwt_refresh_token_expire_days
        )

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": token_type,
    })

    encoded_jwt = jwt.encode(
        to_encode,
        jwt_settings.jwt_secret_key,
        algorithm=jwt_settings.jwt_algorithm,
    )

    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a JWT refresh token.

    Args:
        data: Payload data to encode in the token

    Returns:
        str: Encoded JWT refresh token
    """
    return create_access_token(data, token_type="refresh")


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT token.

    Args:
        token: JWT token string to decode

    Returns:
        Optional[Dict[str, Any]]: Decoded token payload or None if invalid
    """
    settings = get_settings()
    jwt_settings = settings.jwt

    try:
        payload = jwt.decode(
            token,
            jwt_settings.jwt_secret_key,
            algorithms=[jwt_settings.jwt_algorithm],
        )
        return payload
    except JWTError:
        return None


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """Verify a JWT token and check its type.

    Args:
        token: JWT token string to verify
        token_type: Expected token type

    Returns:
        Optional[Dict[str, Any]]: Decoded payload if valid, None otherwise
    """
    payload = decode_token(token)

    if payload is None:
        return None

    if payload.get("type") != token_type:
        return None

    return payload


class TokenData:
    """Token data extracted from JWT."""

    def __init__(
        self,
        sub: str,
        user_id: Optional[str] = None,
        roles: Optional[list[str]] = None,
        exp: Optional[datetime] = None,
    ) -> None:
        self.sub = sub
        self.user_id = user_id or sub
        self.roles = roles or []
        self.exp = exp

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "TokenData":
        """Create TokenData from JWT payload.

        Args:
            payload: Decoded JWT payload

        Returns:
            TokenData: Token data instance
        """
        return cls(
            sub=payload.get("sub", ""),
            user_id=payload.get("user_id"),
            roles=payload.get("roles", []),
            exp=datetime.fromtimestamp(payload.get("exp", 0), tz=timezone.utc),
        )
