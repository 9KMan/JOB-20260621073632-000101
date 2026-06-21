// src/api/schemas/auth.py
"""Authentication schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """JWT Token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """JWT Token payload data."""
    user_id: Optional[str] = None


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """User creation schema."""
    password: str = Field(min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """User update schema."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(default=None, min_length=8, max_length=100)
    is_active: Optional[bool] = None


class UserLogin(BaseModel):
    """User login schema."""
    username: str
    password: str


class UserResponse(UserBase):
    """User response schema."""
    id: UUID
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}
