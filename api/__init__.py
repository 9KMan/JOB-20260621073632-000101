# api/__init__.py
"""API package initialization.

Exports shared schemas and API configuration.
"""

from api.schemas import (
    PaginatedResponse,
    ErrorResponse,
    SuccessResponse,
    BaseFilterParams,
)

__all__ = [
    "PaginatedResponse",
    "ErrorResponse",
    "SuccessResponse",
    "BaseFilterParams",
]
