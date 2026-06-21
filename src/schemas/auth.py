# src/schemas/auth.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    """Token payload schema."""
    sub: str  # User ID
    exp: datetime
    iat: datetime


class UserCreate(BaseModel):
    """User creation schema."""
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """User login schema."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response schema."""
    id: str
    email: str
    full_name: Optional[str]
    is_active: bool
    is_superuser: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}
