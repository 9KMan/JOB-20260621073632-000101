// src/schemas/auth.py
"""Authentication schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    """Login request schema."""

    model_config = ConfigDict(populate_by_name=True)

    email: EmailStr
    password: str = Field(..., min_length=8)


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token payload data."""

    sub: str | None = None
    exp: datetime | None = None
    permissions: list[str] = Field(default_factory=list)


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(default="user", max_length=50)


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """User response schema."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime


class UserMeResponse(BaseModel):
    """Current user response schema."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
