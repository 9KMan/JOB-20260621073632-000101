// api/__init__.py
"""
API package for FastAPI endpoints.

This package contains all API routes, schemas, and utilities.
"""

from api.schemas import (
    ErrorResponse,
    HealthCheck,
    PaginatedResponse,
)

__all__ = [
    "ErrorResponse",
    "HealthCheck",
    "PaginatedResponse",
]
