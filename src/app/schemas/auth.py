// src/app/schemas/auth.py
"""
Authentication schemas.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, ConfigDict

from app.schemas.common import BaseSchema, TimestampMixin


class TokenSchema(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    """Token payload schema."""
    sub: str  # user id
    exp: datetime
    type: str  # access or refresh
    role: Optional[str] = None


class LoginRequest(BaseModel):
    """Login request schema."""
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)


class UserCreate(BaseSchema):
    """User creation schema."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = Field(default=None, max_length=255)
    role: str = Field(default="user", pattern="^(admin|user|reviewer)$")


class UserUpdate(BaseSchema):
    """User update schema."""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(default=None, min_length=3, max_length=100)
    full_name: Optional[str] = Field(default=None, max_length=255)
    role: Optional[str] = Field(default=None, pattern="^(admin|user|reviewer)$")
    is_active: Optional[bool] = None


class UserResponse(BaseSchema, TimestampMixin):
    """User response schema."""
    id: str
    email: str
    username: str
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    role: str
