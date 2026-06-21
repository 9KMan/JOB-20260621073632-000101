# core/security.py
"""Security utilities for JWT and password handling.

Provides JWT token creation/verification and password hashing.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme
bearer_scheme = HTTPBearer(auto_error=False)


class TokenData:
    """JWT token payload data."""
    
    def __init__(
        self,
        sub: str,
        exp: datetime,
        iat: Optional[datetime] = None,
    ) -> None:
        self.sub = sub
        self.exp = exp
        self.iat = iat or datetime.now(timezone.utc)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JWT encoding."""
        return {
            "sub": self.sub,
            "exp": self.exp,
            "iat": self.iat,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "TokenData":
        """Create from decoded JWT dictionary."""
        return cls(
            sub=data.get("sub", ""),
            exp=datetime.fromtimestamp(data.get("exp", 0), tz=timezone.utc),
            iat=datetime.fromtimestamp(data.get("iat", 0), tz=timezone.utc) if data.get("iat") else None,
        )


class TokenPayload:
    """Validated token payload for API use."""
    
    def __init__(
        self,
        user_id: str,
        exp: datetime,
    ) -> None:
        self.user_id = user_id
        self.exp = exp
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.now(timezone.utc) >= self.exp


# User type for dependency injection
CurrentUser = Optional[TokenPayload]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password.
    
    Args:
        plain_password: Plain text password
        hashed_password: Bcrypt hashed password
        
    Returns:
        True if password matches
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Bcrypt hashed password
    """
    return pwd_context.hash(password)


def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[dict] = None,
) -> str:
    """Create a JWT access token.
    
    Args:
        subject: Token subject (typically user_id)
        expires_delta: Optional custom expiration time
        additional_claims: Optional additional JWT claims
        
    Returns:
        Encoded JWT token string
    """
    now = datetime.now(timezone.utc)
    
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.jwt_expiration_minutes)
    
    to_encode = {
        "sub": subject,
        "exp": expire,
        "iat": now,
    }
    
    if additional_claims:
        to_encode.update(additional_claims)
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    
    logger.debug("Access token created for subject: %s", subject)
    return encoded_jwt


def decode_token(token: str) -> TokenPayload:
    """Decode and validate a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        TokenPayload with validated claims
        
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
        
        user_id: str = payload.get("sub")
        exp = payload.get("exp")
        
        if user_id is None or exp is None:
            logger.warning("Token missing required claims")
            raise credentials_exception
        
        exp_datetime = datetime.fromtimestamp(exp, tz=timezone.utc)
        
        return TokenPayload(user_id=user_id, exp=exp_datetime)
        
    except JWTError as e:
        logger.warning("JWT decode error: %s", str(e))
        raise credentials_exception


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> CurrentUser:
    """FastAPI dependency to get current authenticated user.
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        TokenPayload if authenticated, None otherwise
    """
    if credentials is None:
        return None
    
    try:
        return decode_token(credentials.credentials)
    except HTTPException:
        return None


async def require_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> TokenPayload:
    """FastAPI dependency requiring authentication.
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        TokenPayload with user information
        
    Raises:
        HTTPException: If not authenticated
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return decode_token(credentials.credentials)
