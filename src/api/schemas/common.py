// src/api/schemas/common.py
"""Common API schemas."""
from typing import TypeVar, Generic, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime

T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class PaginatedResponse(BaseSchema, Generic[T]):
    """Paginated response wrapper."""

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class ErrorResponse(BaseSchema):
    """Error response schema."""

    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = datetime.utcnow()


class SuccessResponse(BaseSchema):
    """Success response schema."""

    message: str
    data: Optional[dict] = None
    timestamp: datetime = datetime.utcnow()
