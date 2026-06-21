// src/schemas/auth.py
"""Authentication schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import EmailStr, Field, ConfigDict

from src.schemas.common import BaseSchema
from src.models.enums import UserRole


class Token(BaseSchema):
    """JWT Token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseSchema):
    """Token payload data."""
    sub: Optional[str] = None
    user_id: Optional[UUID] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None
    exp: Optional[datetime] = None


class UserBase(BaseSchema):
    """Base user schema."""
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    role: UserRole = UserRole.VIEWER


class UserCreate(UserBase):
    """User creation schema."""
    password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(BaseSchema):
    """User update schema."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[UserRole] = None
    password: Optional[str] = Field(None, min_length=8, max_length=128)
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """User response schema."""
    id: UUID
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseSchema):
    """User login schema."""
    email: EmailStr
    password: str
