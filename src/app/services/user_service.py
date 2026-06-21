// src/app/services/user_service.py
"""
User Service
Handles user-related business logic.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.base import BaseService
from app.core.security import get_password_hash, verify_password


class UserService(BaseService[User]):
    """Service for user operations."""
    
    def __init__(self, session: Optional[AsyncSession] = None):
        super().__init__(User, session)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        session = await self._get_session()
        result = await session.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        session = await self._get_session()
        result = await session.execute(
            select(User).where(User.username == username.lower())
        )
        return result.scalar_one_or_none()
    
    async def create_user(self, data: dict) -> User:
        """Create new user with hashed password."""
        if "password" in data:
            data["hashed_password"] = get_password_hash(data.pop("password"))
        
        if "email" in data:
            data["email"] = data["email"].lower()
        
        if "username" in data:
            data["username"] = data["username"].lower()
        
        return await self.create(data)
    
    async def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password."""
        user = await self.get_by_username(username)
        if not user:
            return None
        
        if not user.is_active:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    async def update_password(self, user_id: UUID, new_password: str) -> bool:
        """Update user password."""
        hashed = get_password_hash(new_password)
        session = await self._get_session()
        from sqlalchemy import update as sql_update
        await session.execute(
            sql_update(User)
            .where(User.id == user_id)
            .values(hashed_password=hashed)
        )
        await session.flush()
        return True
