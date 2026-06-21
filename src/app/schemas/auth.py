// src/app/schemas/auth.py
"""Authentication schemas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Token(BaseModel):
    """JWT token response."""
    
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token payload data."""
    
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None


class UserBase(BaseModel):
    """Base user schema."""
    
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)


class UserCreate(UserBase):
    """User creation schema."""
    
    password: str = Field(min_length=8, max_length=100)
    role: Optional[str] = "user"


class UserLogin(BaseModel):
    """User login schema."""
    
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """User update schema."""
    
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    password: Optional[str] = Field(default=None, min_length=8, max_length=100)
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """User response schema."""
    
    id: str
    is_active: bool = True
    is_superuser: bool = False
    role: str = "user"
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    """User list response with pagination."""
    
    users: list[UserResponse]
    total: int
    page: int
    page_size: int
