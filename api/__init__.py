// api/__init__.py
"""API module for FastAPI endpoints and schemas."""
from api.schemas import (
    ErrorResponse,
    HealthResponse,
    PaginatedResponse,
    PaginationParams,
)

__all__ = [
    "ErrorResponse",
    "HealthResponse",
    "PaginatedResponse",
    "PaginationParams",
]
