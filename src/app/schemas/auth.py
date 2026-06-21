// src/app/schemas/auth.py
"""Authentication schemas."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Token(BaseModel):
    """Token response schema."""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Token payload schema."""

    sub: str
    exp: int


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)


class UserCreate(UserBase):
    """User creation schema."""

    password: str = Field(min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """User update schema."""

    email: EmailStr | None = None
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=100)
    is_active: bool | None = None


class UserResponse(UserBase):
    """User response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    is_active: bool
    is_superuser: bool
    created_at: str
    updated_at: str


class UserLogin(BaseModel):
    """User login schema."""

    username: EmailStr
    password: str
