# src/api/__init__.py
"""API module for FastAPI endpoints."""

from api.schemas import (
    PaginatedResponse,
    ErrorResponse,
    HealthResponse,
)

__all__ = [
    "PaginatedResponse",
    "ErrorResponse",
    "HealthResponse",
]
