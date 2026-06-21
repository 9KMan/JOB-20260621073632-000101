// src/app/services/user_service.py
"""User service for authentication and user management."""
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AuthenticationException,
    DuplicateException,
    NotFoundException,
)
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.auth import UserCreate, UserUpdate
from app.services.base import BaseService


class UserService(BaseService[User]):
    """Service for user management."""

    def __init__(self, session: AsyncSession):
        """Initialize user service."""
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by email."""
        query = select(User).where(User.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id(self, id: UUID) -> User:
        """Get a user by ID."""
        query = select(User).where(User.id == id)
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundException("User", str(id))
        return user

    async def create(self, data: UserCreate) -> User:
        """Create a new user."""
        # Check for duplicate email
        existing = await self.get_by_email(data.email)
        if existing:
            raise DuplicateException("User", "email", data.email)

        # Hash password
        hashed_password = get_password_hash(data.password)

        # Create user
        user = User(
            email=data.email,
            hashed_password=hashed_password,
            full_name=data.full_name,
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def update(self, id: UUID, data: UserUpdate) -> User:
        """Update a user."""
        user = await self.get_by_id(id)

        if data.email and data.email != user.email:
            existing = await self.get_by_email(data.email)
            if existing:
                raise DuplicateException("User", "email", data.email)
            user.email = data.email

        if data.full_name:
            user.full_name = data.full_name

        if data.password:
            user.hashed_password = get_password_hash(data.password)

        if data.is_active is not None:
            user.is_active = data.is_active

        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def authenticate(self, email: str, password: str) -> User:
        """Authenticate a user."""
        user = await self.get_by_email(email)
        if not user:
            raise AuthenticationException("Invalid email or password")
        if not verify_password(password, user.hashed_password):
            raise AuthenticationException("Invalid email or password")
        if not user.is_active:
            raise AuthenticationException("User account is disabled")
        return user

    async def delete(self, id: UUID) -> bool:
        """Soft delete a user."""
        user = await self.get_by_id(id)
        user.is_deleted = True
        user.is_active = False
        await self.session.flush()
        return True
