// app/api/__init__.py
"""API package containing route modules and shared schemas."""

from app.api.schemas import (
    PaginationParams,
    create_pagination_response,
)

__all__ = [
    "PaginationParams",
    "create_pagination_response",
]
