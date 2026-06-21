# src/schemas/user.py
"""User Pydantic schemas."""
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """JWT Token schema."""
    
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")


class TokenData(BaseModel):
    """Token data schema."""
    
    username: Optional[str] = Field(None, description="Username from token")


class UserBase(BaseModel):
    """Base user schema."""
    
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    full_name: Optional[str] = Field(None, max_length=255, description="Full name")


class UserCreate(UserBase):
    """User creation schema."""
    
    password: str = Field(..., min_length=8, description="Password")
    is_superuser: bool = Field(default=False, description="Is superuser flag")


class UserUpdate(BaseModel):
    """User update schema."""
    
    email: Optional[EmailStr] = Field(None, description="Email address")
    full_name: Optional[str] = Field(None, max_length=255, description="Full name")
    password: Optional[str] = Field(None, min_length=8, description="Password")
    is_active: Optional[bool] = Field(None, description="Is active flag")


class UserResponse(UserBase):
    """User response schema."""
    
    id: UUID
    is_active: bool
    is_superuser: bool
    created_at: str
    updated_at: str
    
    model_config = {"from_attributes": True}


class UserInDB(UserBase):
    """User in database schema."""
    
    id: UUID
    hashed_password: str
    is_active: bool
    is_superuser: bool
    created_at: str
    updated_at: str
    
    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    """Login request schema."""
    
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")
