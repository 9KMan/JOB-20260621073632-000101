// core/security.py
"""Security utilities for JWT authentication and password hashing.

Provides secure password hashing using bcrypt and JWT token generation
using HS256 algorithm as specified in the project requirements.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import get_settings

logger = logging.getLogger(__name__)

# Password hashing context using bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # Cost factor for bcrypt
)

# Settings cache
_settings = get_settings


def get_jwt_settings() -> Any:
    """Get JWT settings (lazy loaded)."""
    return _settings().jwt


def get_app_settings() -> Any:
    """Get app settings (lazy loaded)."""
    return _settings()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password.
    
    Uses bcrypt for secure comparison that is resistant to timing attacks.
    
    Args:
        plain_password: The plain text password to verify.
        hashed_password: The bcrypt hashed password to compare against.
    
    Returns:
        bool: True if password matches, False otherwise.
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.warning(f"Password verification failed: {e}")
        return False


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt.
    
    Creates a secure hash of the password that can be stored
    in the database for later verification.
    
    Args:
        password: The plain text password to hash.
    
    Returns:
        str: The bcrypt hashed password.
    """
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
    token_type: str = "access",
) -> str:
    """Create a JWT access token.
    
    Generates a JSON Web Token signed with HS256 algorithm.
    The token includes standard claims and any additional data provided.
    
    Args:
        data: Dictionary of claims to include in the token payload.
        expires_delta: Optional custom expiration time delta.
        token_type: Type of token ('access' or 'refresh').
    
    Returns:
        str: The encoded JWT token.
    """
    settings = get_app_settings()
    jwt_settings = get_jwt_settings()

    # Create a copy of the data to avoid modifying the original
    to_encode = data.copy()

    # Calculate expiration time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        if token_type == "refresh":
            expire = datetime.now(timezone.utc) + timedelta(
                days=jwt_settings.jwt_refresh_token_expire_days
            )
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=jwt_settings.jwt_access_token_expire_minutes
            )

    # Add standard claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": token_type,
    })

    # Encode and sign the token
    encoded_jwt = jwt.encode(
        claims=to_encode,
        key=jwt_settings.jwt_secret_key,
        algorithm=jwt_settings.jwt_algorithm,
    )

    return encoded_jwt


def decode_token(token: str, verify_exp: bool = True) -> Optional[Dict[str, Any]]:
    """Decode and verify a JWT token.
    
    Validates the token signature and optionally the expiration time.
    
    Args:
        token: The JWT token string to decode.
        verify_exp: Whether to verify token expiration.
    
    Returns:
        Optional[Dict[str, Any]]: The decoded token payload if valid, None otherwise.
    """
    settings = get_app_settings()
    jwt_settings = get_jwt_settings()

    try:
        payload = jwt.decode(
            token,
            key=jwt_settings.jwt_secret_key,
            algorithms=[jwt_settings.jwt_algorithm],
            options={"verify_exp": verify_exp},
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        return None


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a JWT refresh token.
    
    Refresh tokens have a longer expiration time than access tokens
    and are used to obtain new access tokens.
    
    Args:
        data: Dictionary of claims to include in the token payload.
    
    Returns:
        str: The encoded JWT refresh token.
    """
    return create_access_token(data, token_type="refresh")


def get_token_payload(token: str) -> Optional["JWTPayload"]:
    """Extract and validate token payload.
    
    Args:
        token: The JWT token string.
    
    Returns:
        Optional[JWTPayload]: Validated payload or None.
    """
    from core.security import JWTPayload
    
    payload = decode_token(token)
    if payload is None:
        return None

    return JWTPayload(**payload)


class JWTPayload:
    """JWT Token payload model.
    
    Represents the claims stored in a JWT token.
    """
    
    def __init__(
        self,
        sub: str,
        exp: datetime,
        iat: datetime,
        type: str = "access",
        **extra: Any,
    ) -> None:
        self.sub = sub  # Subject (usually user ID)
        self.exp = exp  # Expiration time
        self.iat = iat  # Issued at
        self.type = type  # Token type
        self.extra = extra  # Additional claims
    
    @property
    def user_id(self) -> str:
        """Get user ID from subject claim."""
        return self.sub
    
    @property
    def is_access_token(self) -> bool:
        """Check if this is an access token."""
        return self.type == "access"
    
    @property
    def is_refresh_token(self) -> bool:
        """Check if this is a refresh token."""
        return self.type == "refresh"
    
    def is_expired(self) -> bool:
        """Check if the token is expired."""
        return datetime.now(timezone.utc) > self.exp
    
    @classmethod
    def from_token(cls, token: str) -> Optional["JWTPayload"]:
        """Create JWTPayload from token string.
        
        Args:
            token: JWT token string.
        
        Returns:
            JWTPayload instance if token is valid, None otherwise.
        """
        payload = decode_token(token)
        if payload is None:
            return None
        
        return cls(**payload)


# Import for type hints
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import Depends, HTTPException, status
    from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
    from sqlalchemy.ext.asyncio import AsyncSession

    security = HTTPBearer()


async def get_current_user(
    credentials: "HTTPAuthorizationCredentials" = Depends(security),
) -> Dict[str, Any]:
    """FastAPI dependency to get the current authenticated user.
    
    Extracts and validates the JWT token from the Authorization header,
    then returns the user information from the token payload.
    
    Args:
        credentials: HTTP Bearer token credentials.
    
    Returns:
        Dict containing user information from the token.
    
    Raises:
        HTTPException: If token is invalid or expired.
    """
    from fastapi import HTTPException, status
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(credentials.credentials)
    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # You could add database lookup here to get full user info
    # For now, we just return what's in the token
    return {
        "user_id": user_id,
        "email": payload.get("email"),
        "roles": payload.get("roles", []),
    }


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Verify that the current user is active.
    
    Can be extended to check user status in database.
    
    Args:
        current_user: Current authenticated user from get_current_user.
    
    Returns:
        Dict containing active user information.
    """
    # Add any active status checks here
    # For example, check if user.is_active in database
    return current_user


def create_token_pair(user_id: str, additional_claims: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """Create both access and refresh tokens for a user.
    
    Convenience function to generate a complete token pair
    for authentication flows.
    
    Args:
        user_id: The user's unique identifier.
        additional_claims: Optional additional claims to include.
    
    Returns:
        Dict with 'access_token' and 'refresh_token' keys.
    """
    base_claims = {"sub": user_id}
    if additional_claims:
        base_claims.update(additional_claims)

    return {
        "access_token": create_access_token(base_claims),
        "refresh_token": create_refresh_token(base_claims),
        "token_type": "bearer",
    }
