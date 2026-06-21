# api/__init__.py
"""API module for FastAPI routes and schemas.

This module contains the API layer including:
- Shared Pydantic schemas for request/response validation
- Versioned API routes
"""

from api.schemas import (
    BaseResponse,
    PaginatedResponse,
    ErrorResponse,
    HealthCheckResponse,
)

__all__ = [
    "BaseResponse",
    "PaginatedResponse",
    "ErrorResponse",
    "HealthCheckResponse",
]
