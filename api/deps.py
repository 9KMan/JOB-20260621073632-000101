// api/deps.py
"""API dependencies for dependency injection."""

from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from api.schemas.auth import TokenData

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> TokenData:
    """
    Get current user from JWT token.
    
    Args:
        credentials: HTTP Bearer token credentials
        
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
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        
        if user_id is None:
            raise credentials_exception
            
        return TokenData(user_id=user_id, email=email)
        
    except JWTError:
        raise credentials_exception


async def get_current_active_user(
    current_user: Annotated[TokenData, Depends(get_current_user)],
) -> TokenData:
    """
    Get current active user.
    
    Args:
        current_user: Current user from token
        
    Returns:
        TokenData: Current active user
    """
    # In a real implementation, you would verify the user exists and is active
    return current_user


async def get_current_superuser(
    current_user: Annotated[TokenData, Depends(get_current_active_user)],
) -> TokenData:
    """
    Get current superuser (admin).
    
    Args:
        current_user: Current user from token
        
    Returns:
        TokenData: Current superuser
        
    Raises:
        HTTPException: If user is not a superuser
    """
    # In a real implementation, you would check is_superuser from the database
    # For now, we'll skip this check
    return current_user


# Type aliases for cleaner dependency injection
CurrentUser = Annotated[TokenData, Depends(get_current_user)]
CurrentActiveUser = Annotated[TokenData, Depends(get_current_active_user)]
CurrentSuperUser = Annotated[TokenData, Depends(get_current_superuser)]
DbSession = Annotated[AsyncSession, Depends(get_db)]
