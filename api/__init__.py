# api/__init__.py
"""
API package initialization.

Exposes the API router and shared schemas.
"""

from api.schemas import BaseResponse, ErrorResponse, PaginatedResponse

__all__ = [
    "BaseResponse",
    "ErrorResponse",
    "PaginatedResponse",
]
