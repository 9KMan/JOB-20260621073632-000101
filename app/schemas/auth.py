# app/schemas/auth.py
"""Authentication schemas."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class Token(BaseModel):
    """JWT Token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """JWT Token payload data."""

    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None


class UserLogin(BaseModel):
    """User login request."""

    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8)


class UserCreate(BaseModel):
    """User creation request."""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    role: str = Field(default="user", pattern="^(user|admin|reviewer)$")


class UserUpdate(BaseModel):
    """User update request."""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = Field(default=None, pattern="^(user|admin|reviewer)$")


class UserResponse(BaseModel):
    """User response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    username: str
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    role: str
    created_at: datetime
    updated_at: datetime
