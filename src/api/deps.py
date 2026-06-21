// src/api/deps.py
"""API dependencies."""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.database import get_db

settings = get_settings()
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> dict:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return {"user_id": user_id, "email": payload.get("email")}
    except JWTError:
        raise credentials_exception


# Type aliases for dependency injection
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[dict, Depends(get_current_user)]
