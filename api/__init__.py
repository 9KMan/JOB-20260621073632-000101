# api/__init__.py
"""API module for AP Automation Engine.

Provides REST API endpoints and Pydantic schemas.
"""

from api.schemas import (
    HealthResponse,
    ErrorResponse,
    PaginationParams,
    PaginatedResponse,
)

__all__ = [
    "HealthResponse",
    "ErrorResponse",
    "PaginationParams",
    "PaginatedResponse",
]
