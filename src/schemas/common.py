// src/schemas/common.py
"""Common schemas."""
from datetime import datetime
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class Token(BaseModel):
    """Token schema."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data schema."""
    user_id: UUID | None = None
    email: str | None = None


class PaginatedResponse(BaseModel, Generic[T := TypeVar("T")]):
    """Paginated response."""
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class BaseSchema(BaseModel):
    """Base schema configuration."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class TimestampSchema(BaseSchema):
    """Schema with timestamps."""
    created_at: datetime
    updated_at: datetime


class UUIDSchema(BaseSchema):
    """Schema with UUID."""
    id: UUID
