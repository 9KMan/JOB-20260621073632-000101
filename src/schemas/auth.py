// src/schemas/auth.py
"""Authentication schemas."""
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.schemas.common import BaseSchema, TimestampMixin


class Token(BaseSchema):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseSchema):
    """Token payload data."""
    user_id: Optional[UUID] = None
    email: Optional[str] = None
    is_superuser: bool = False


class UserBase(BaseSchema):
    """Base user schema."""
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str = Field(..., min_length=8)


class UserUpdate(BaseSchema):
    """Schema for updating a user."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None


class UserResponse(UserBase, TimestampMixin):
    """Schema for user response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    is_active: bool
    is_superuser: bool


class LoginRequest(BaseSchema):
    """Login request schema."""
    username: str = Field(..., min_length=1)  # email as username
    password: str = Field(..., min_length=1)
