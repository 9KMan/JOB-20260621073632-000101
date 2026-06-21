# src/services/auth_service.py
from typing import Optional

from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from src.models.user import User
from src.api.v1.schemas.auth import UserCreate, UserResponse


class AuthService:
    """Service for authentication and user management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user by username and password."""
        user = await self.get_user_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user

    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        # Check if username or email already exists
        existing_user = await self.get_user_by_username(user_data.username)
        if existing_user:
            raise ValueError("Username already registered")
        
        existing_email = await self.get_user_by_email(user_data.email)
        if existing_email:
            raise ValueError("Email already registered")

        # Create new user
        user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=get_password_hash(user_data.password),
            role=user_data.role,
            is_active=True,
            is_superuser=False,
        )
        
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        
        return user

    def create_tokens(self, user: User) -> dict:
        """Create access and refresh tokens for a user."""
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role,
        }
        
        return {
            "access_token": create_access_token(token_data),
            "refresh_token": create_refresh_token(token_data),
            "token_type": "bearer",
        }

    async def refresh_access_token(self, refresh_token: str) -> Optional[dict]:
        """Refresh access token using refresh token."""
        try:
            payload = decode_token(refresh_token)
            if not payload or payload.get("type") != "refresh":
                return None
            
            user_id = payload.get("sub")
            if not user_id:
                return None
            
            user = await self.get_user_by_id(user_id)
            if not user or not user.is_active:
                return None
            
            return self.create_tokens(user)
        except JWTError:
            return None

    async def update_user(self, user: User, **kwargs) -> User:
        """Update user information."""
        if "password" in kwargs:
            kwargs["hashed_password"] = get_password_hash(kwargs.pop("password"))
        
        for key, value in kwargs.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)
        
        await self.db.flush()
        await self.db.refresh(user)
        
        return user

    async def deactivate_user(self, user: User) -> User:
        """Deactivate a user."""
        user.is_active = False
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def activate_user(self, user: User) -> User:
        """Activate a user."""
        user.is_active = True
        await self.db.flush()
        await self.db.refresh(user)
        return user
