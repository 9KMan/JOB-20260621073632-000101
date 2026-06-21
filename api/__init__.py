# api/__init__.py
"""API package initialization."""

from api.schemas import (
    BaseResponse,
    PaginatedResponse,
    ErrorResponse,
    HealthResponse,
)

__all__ = [
    "BaseResponse",
    "PaginatedResponse",
    "ErrorResponse",
    "HealthResponse",
]
