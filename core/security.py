# core/security.py
"""
JWT (HS256) and bcrypt password utilities.

Provides token creation/verification and password hashing.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import settings

# Password hashing context (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token security scheme
bearer_scheme = HTTPBearer(auto_error=True)


class JWTPayload:
    """
    Decoded JWT token payload.
    
    Attributes:
        sub: Subject (user ID or identifier)
        exp: Expiration timestamp
        iat: Issued-at timestamp
        type: Token type ("access" or "refresh")
        permissions: List of permission strings
    """

    def __init__(
        self,
        sub: str,
        exp: datetime,
        iat: datetime | None = None,
        type: str = "access",
        permissions: list[str] | None = None,
        **extra: Any,
    ) -> None:
        self.sub = sub
        self.exp = exp
        self.iat = iat or datetime.now(timezone.utc)
        self.type = type
        self.permissions = permissions or []
        self.extra = extra

    def to_dict(self) -> dict[str, Any]:
        """Convert payload to dictionary for encoding."""
        data = {
            "sub": self.sub,
            "exp": self.exp,
            "iat": self.iat,
            "type": self.type,
            "permissions": self.permissions,
        }
        data.update(self.extra)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JWTPayload":
        """Create payload from decoded token dict."""
        return cls(
            sub=data.get("sub", ""),
            exp=datetime.fromtimestamp(data.get("exp", 0), tz=timezone.utc),
            iat=datetime.fromtimestamp(data.get("iat", 0), tz=timezone.utc)
            if data.get("iat")
            else None,
            type=data.get("type", "access"),
            permissions=data.get("permissions", []),
            **{k: v for k, v in data.items() if k not in ("sub", "exp", "iat", "type", "permissions")},
        )


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password.
        
    Returns:
        Bcrypt hash of the password.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a bcrypt hash.
    
    Args:
        plain_password: Plain text password to verify.
        hashed_password: Bcrypt hash to verify against.
        
    Returns:
        True if password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
    token_type: str = "access",
    permissions: list[str] | None = None,
    **extra_claims: Any,
) -> str:
    """
    Create a JWT access token.
    
    Args:
        subject: Token subject (typically user ID).
        expires_delta: Optional custom expiry time.
        token_type: Token type ("access" or "refresh").
        permissions: List of permission strings.
        **extra_claims: Additional claims to include in token.
        
    Returns:
        Encoded JWT token string.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt.access_token_expire_minutes
        )

    payload = JWTPayload(
        sub=subject,
        exp=expire,
        type=token_type,
        permissions=permissions or [],
        **extra_claims,
    )

    return jwt.encode(
        payload.to_dict(),
        settings.jwt.secret_key.get_secret_value(),
        algorithm=settings.jwt.algorithm,
    )


def create_refresh_token(subject: str, **extra_claims: Any) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        subject: Token subject (typically user ID).
        **extra_claims: Additional claims.
        
    Returns:
        Encoded JWT refresh token string.
    """
    expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt.refresh_token_expire_days)
    payload = JWTPayload(
        sub=subject,
        exp=expire,
        type="refresh",
        **extra_claims,
    )
    return jwt.encode(
        payload.to_dict(),
        settings.jwt.secret_key.get_secret_value(),
        algorithm=settings.jwt.algorithm,
    )


def decode_token(token: str) -> JWTPayload:
    """
    Decode and verify a JWT token.
    
    Args:
        token: Encoded JWT token string.
        
    Returns:
        Decoded JWTPayload.
        
    Raises:
        JWTError: If token is invalid or expired.
    """
    payload = jwt.decode(
        token,
        settings.jwt.secret_key.get_secret_value(),
        algorithms=[settings.jwt.algorithm],
    )
    return JWTPayload.from_dict(payload)


def verify_token(token: str) -> JWTPayload | None:
    """
    Verify a JWT token and return payload if valid.
    
    Args:
        token: Encoded JWT token string.
        
    Returns:
        JWTPayload if valid, None if invalid/expired.
    """
    try:
        return decode_token(token)
    except JWTError:
        return None


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> JWTPayload:
    """
    FastAPI dependency to extract and validate the current user from JWT.
    
    Args:
        credentials: Bearer token from Authorization header.
        
    Returns:
        Validated JWTPayload.
        
    Raises:
        HTTPException: If token is invalid or expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(credentials.credentials)
        if payload.sub is None:
            raise credentials_exception
        if payload.exp < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError:
        raise credentials_exception


async def get_current_active_user(
    current_user: Annotated[JWTPayload, Depends(get_current_user)],
) -> JWTPayload:
    """
    FastAPI dependency to get the current active user.
    
    Can be extended to check user status, permissions, etc.
    """
    return current_user


def require_permission(*required_permissions: str):
    """
    Dependency factory for permission checking.
    
    Usage:
        @app.post("/admin")
        async def admin_endpoint(user: JWTPayload = Depends(require_permission("admin"))):
            ...
    """
    async def permission_checker(
        current_user: Annotated[JWTPayload, Depends(get_current_user)],
    ) -> JWTPayload:
        for perm in required_permissions:
            if perm not in current_user.permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permission: {perm}",
                )
        return current_user
    return permission_checker
