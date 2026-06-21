// src/app/schemas/user.py
"""
User schemas for API request/response validation.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.base import BaseSchema, TimestampSchema


# Request schemas
class UserCreate(BaseSchema):
    """Schema for creating a user."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(default="user")
    
    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if not v.isalnum() and "_" not in v:
            raise ValueError("Username must be alphanumeric with optional underscores")
        return v.lower()


class UserUpdate(BaseSchema):
    """Schema for updating a user."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserPasswordUpdate(BaseSchema):
    """Schema for password update."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


# Response schemas
class UserResponse(TimestampSchema):
    """User response schema."""
    id: UUID
    email: str
    username: str
    full_name: str
    is_active: bool
    is_superuser: bool
    role: str


class UserBrief(BaseSchema):
    """Brief user information."""
    id: UUID
    username: str
    full_name: str


# Auth schemas
class Token(BaseSchema):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseSchema):
    """JWT token payload schema."""
    sub: str
    exp: datetime
    type: str


class LoginRequest(BaseSchema):
    """Login request schema."""
    username: str
    password: str


class RefreshTokenRequest(BaseSchema):
    """Refresh token request schema."""
    refresh_token: str
