// api/schemas/auth.py
"""Authentication Pydantic schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """JWT Token response schema."""
    
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token payload data."""
    
    user_id: Optional[UUID] = None
    email: Optional[str] = None
    exp: Optional[datetime] = None


class UserLogin(BaseModel):
    """User login request schema."""
    
    email: EmailStr
    password: str = Field(min_length=6)


class UserCreate(BaseModel):
    """User creation request schema."""
    
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    full_name: str = Field(min_length=1, max_length=255)
    is_superuser: bool = False


class UserUpdate(BaseModel):
    """User update request schema."""
    
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """User response schema."""
    
    id: UUID
    email: str
    full_name: str
    is_active: bool
    is_superuser: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class PasswordChange(BaseModel):
    """Password change request schema."""
    
    current_password: str
    new_password: str = Field(min_length=8, max_length=100)
