# api/__init__.py
"""API module for AP Automation Engine.

This module contains API routes, schemas, and versioned endpoints.
"""

from api.schemas import (
    BaseResponse,
    ErrorResponse,
    PaginatedResponse,
    PaginationParams,
)

__all__ = [
    "BaseResponse",
    "ErrorResponse",
    "PaginatedResponse",
    "PaginationParams",
]
