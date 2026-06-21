// src/api/dependencies.py
"""FastAPI dependencies for authentication and database."""
from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.config import get_settings
from src.database import get_async_db
from src.models.user import User

settings = get_settings()
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_async_db)],
) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token,
            settings.jwt.secret_key,
            algorithms=[settings.jwt.algorithm],
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise credentials_exception
    
    result = await db.execute(
        select(User)
        .options(selectinload(User.purchase_orders))
        .where(User.id == user_uuid)
        .where(User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def get_current_superuser(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """Get current superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user


CurrentUser = Annotated[User, Depends(get_current_active_user)]
SuperUser = Annotated[User, Depends(get_current_superuser)]
DbSession = Annotated[AsyncSession, Depends(get_async_db)]
