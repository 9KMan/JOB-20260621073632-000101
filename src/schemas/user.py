// src/schemas/user.py
"""User schemas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.schemas.base import BaseSchema


class UserBase(BaseSchema):
    """Base user schema."""
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    full_name: Optional[str] = None
    role: str = "user"


class UserCreate(UserBase):
    """User creation schema."""
    password: str = Field(min_length=8, max_length=100)
    is_superuser: bool = False


class UserUpdate(BaseSchema):
    """User update schema."""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(default=None, min_length=3, max_length=100)
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(default=None, min_length=8, max_length=100)


class UserResponse(UserBase):
    """User response schema."""
    id: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime


class UserLogin(BaseSchema):
    """User login schema."""
    username: str
    password: str


class Token(BaseSchema):
    """Token response schema."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseSchema):
    """Token data schema."""
    user_id: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None
