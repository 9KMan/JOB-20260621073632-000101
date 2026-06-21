# api/__init__.py
"""API module for AP Automation Engine.

This module contains the API layer with FastAPI routers,
Pydantic schemas, and endpoint definitions.
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
