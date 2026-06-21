// src/schemas/user.py
"""User-related Pydantic schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.schemas.base import BaseSchema, TimestampMixin


class UserBase(BaseSchema):
    """Base user schema."""

    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    full_name: Optional[str] = Field(default=None, max_length=255)


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(min_length=8, max_length=100)
    is_superuser: bool = False


class UserUpdate(BaseSchema):
    """Schema for updating a user."""

    email: Optional[EmailStr] = None
    username: Optional[str] = Field(default=None, min_length=3, max_length=100)
    full_name: Optional[str] = Field(default=None, max_length=255)
    password: Optional[str] = Field(default=None, min_length=8, max_length=100)
    is_active: Optional[bool] = None


class UserResponse(UserBase, TimestampMixin):
    """Schema for user response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool
    is_superuser: bool


class UserLogin(BaseSchema):
    """Schema for user login."""

    username: str
    password: str


class Token(BaseSchema):
    """Schema for JWT token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseSchema):
    """Schema for token payload data."""

    sub: Optional[str] = None
    exp: Optional[datetime] = None
    type: str = "access"
