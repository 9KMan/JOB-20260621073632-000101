// src/schemas/user.py
"""User schemas."""
from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import EmailStr, Field, ConfigDict

from src.schemas.base import BaseSchema, TimestampUUIDSchema
from src.models.enums import UserRole


class UserBase(BaseSchema):
    """Base user schema."""
    
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    role: UserRole = UserRole.VIEWER


class UserCreate(UserBase):
    """Schema for creating a user."""
    
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseSchema):
    """Schema for updating a user."""
    
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(TimestampUUIDSchema):
    """Schema for user response."""
    
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool


class UserLogin(BaseSchema):
    """Schema for user login."""
    
    email: EmailStr
    password: str
