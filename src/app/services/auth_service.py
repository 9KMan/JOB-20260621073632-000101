// src/app/services/auth_service.py
"""
Authentication service.
"""
from typing import Optional
from datetime import timedelta, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.auth import UserCreate, UserUpdate
from app.services.base_service import BaseService
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.config import settings


class AuthService(BaseService[User]):
    """Service for authentication operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def authenticate(
        self, username: str, password: str
    ) -> Optional[User]:
        """Authenticate a user by username and password."""
        user = await self.get_by("username", username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return await self.get_by("email", email)

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return await self.get_by("username", username)

    async def create_user(self, user_in: UserCreate) -> User:
        """Create a new user."""
        # Check if email exists
        if await self.get_by_email(user_in.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        # Check if username exists
        if await self.get_by_username(user_in.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken",
            )
        # Create user
        user_data = user_in.model_dump()
        user_data["hashed_password"] = get_password_hash(user_data.pop("password"))
        return await self.create(user_data)

    async def update_user(self, id: UUID, user_in: UserUpdate) -> Optional[User]:
        """Update a user."""
        update_data = user_in.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(
                update_data.pop("password")
            )
        return await self.update(id, update_data)

    def create_tokens(self, user: User) -> dict:
        """Create access and refresh tokens for a user."""
        token_data = {
            "sub": str(user.id),
            "role": user.role,
            "username": user.username,
        }
        access_token = create_access_token(
            token_data,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        refresh_token = create_refresh_token(
            token_data,
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    def verify_access_token(self, token: str) -> Optional[dict]:
        """Verify an access token."""
        payload = decode_token(token)
        if payload and payload.get("type") == "access":
            return payload
        return None

    def verify_refresh_token(self, token: str) -> Optional[dict]:
        """Verify a refresh token."""
        payload = decode_token(token)
        if payload and payload.get("type") == "refresh":
            return payload
        return None

    async def refresh_tokens(self, refresh_token: str) -> Optional[dict]:
        """Refresh access token using refresh token."""
        payload = self.verify_refresh_token(refresh_token)
        if not payload:
            return None
        user = await self.get(UUID(payload["sub"]))
        if not user or not user.is_active:
            return None
        return self.create_tokens(user)
