# src/api/v1/schemas/auth.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class Token(BaseModel):
    """JWT Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """JWT Token payload schema."""
    sub: str
    exp: datetime
    type: str


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    role: str = Field(default="user", max_length=50)


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    role: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)


class UserInDB(UserBase):
    """Schema for user stored in database."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime


class UserResponse(UserBase):
    """Schema for user response."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime


class LoginRequest(BaseModel):
    """Schema for login request."""
    username: str
    password: str


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str
