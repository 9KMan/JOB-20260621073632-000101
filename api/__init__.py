# api/__init__.py
"""API package initialization."""
from api.schemas import (
    ErrorResponse,
    HealthCheckResponse,
    PaginatedResponse,
    PaginationParams,
)

__all__ = [
    "ErrorResponse",
    "HealthCheckResponse",
    "PaginatedResponse",
    "PaginationParams",
]
