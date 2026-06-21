// src/api/schemas/auth.py
"""Authentication schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """JWT token payload."""
    sub: str
    exp: datetime
    type: str


class UserLogin(BaseModel):
    """User login request."""
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserCreate(BaseModel):
    """User creation request."""
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=1, max_length=255)
    is_superuser: bool = False


class UserResponse(BaseModel):
    """User response."""
    id: str
    email: str
    full_name: str
    is_active: bool
    is_superuser: bool
    last_login: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str
