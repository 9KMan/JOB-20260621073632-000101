# api/__init__.py
"""API module for AP Automation Engine.

This package contains the FastAPI application, routers, and schemas.
"""

from api.schemas import (
    HealthCheckResponse,
    ErrorResponse,
    PaginationParams,
    PaginatedResponse,
)

__all__ = [
    "HealthCheckResponse",
    "ErrorResponse",
    "PaginationParams",
    "PaginatedResponse",
]
