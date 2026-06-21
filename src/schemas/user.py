// src/schemas/user.py
"""User schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.schemas.common import BaseSchema, TimestampSchema


class UserBase(BaseSchema):
    """Base user schema."""
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """User creation schema."""
    password: str = Field(min_length=8, max_length=100)


class UserUpdate(BaseSchema):
    """User update schema."""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(default=None, min_length=3, max_length=100)
    full_name: Optional[str] = None
    password: Optional[str] = Field(default=None, min_length=8, max_length=100)
    is_active: Optional[bool] = None


class UserResponse(UserBase, TimestampSchema):
    """User response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    is_active: bool
    is_superuser: bool


class UserInDB(UserResponse):
    """User in database schema."""
    hashed_password: str
