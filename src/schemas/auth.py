// src/schemas/auth.py
"""Authentication schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from src.schemas.common import BaseSchema, TimestampMixin


class UserBase(BaseSchema):
    """Base user schema."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    full_name: Optional[str] = None
    role: str = "user"


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseSchema):
    """Schema for updating a user."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase, TimestampMixin):
    """Schema for user response."""
    id: UUID
    is_active: bool
    is_superuser: bool

    model_config = ConfigDict(from_attributes=True)


class TokenPayload(BaseModel):
    """JWT token payload."""
    sub: str
    exp: datetime
    type: str = "access"


class Token(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefresh(BaseModel):
    """Token refresh request."""
    refresh_token: str


class LoginRequest(BaseModel):
    """Login request schema."""
    username: str
    password: str


class PasswordChange(BaseModel):
    """Password change request."""
    current_password: str
    new_password: str = Field(..., min_length=8)
