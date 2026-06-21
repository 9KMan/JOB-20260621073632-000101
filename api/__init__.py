# api/__init__.py
"""API package for AP Automation Engine."""

from api.schemas import (
    PaginatedResponse,
    ErrorResponse,
    SuccessResponse,
)

__all__ = [
    "PaginatedResponse",
    "ErrorResponse",
    "SuccessResponse",
]
