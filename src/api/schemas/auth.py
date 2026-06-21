// src/api/schemas/auth.py
"""Authentication schemas."""
import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from src.models.user import UserRole


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")


class UserLogin(BaseModel):
    """User login schema."""

    username: str = Field(..., min_length=3, max_length=100, description="Username")
    password: str = Field(..., min_length=8, description="Password")


class UserCreate(BaseModel):
    """User creation schema."""

    username: str = Field(
        ...,
        min_length=3,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="Username (alphanumeric and underscore only)",
    )
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Password")
    full_name: str | None = Field(default=None, max_length=255, description="Full name")
    role: UserRole = Field(default=UserRole.VIEWER, description="User role")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserResponse(BaseModel):
    """User response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    full_name: str | None = Field(default=None, description="Full name")
    role: UserRole = Field(..., description="User role")
    is_active: bool = Field(..., description="Is user active")
    is_superuser: bool = Field(..., description="Is superuser")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class UserUpdate(BaseModel):
    """User update schema."""

    email: EmailStr | None = Field(default=None, description="Email address")
    full_name: str | None = Field(default=None, max_length=255, description="Full name")
    password: str | None = Field(default=None, min_length=8, description="Password")
    role: UserRole | None = Field(default=None, description="User role")
    is_active: bool | None = Field(default=None, description="Is user active")
