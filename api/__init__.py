# api/__init__.py
"""API module for AP Automation Engine.

This package contains FastAPI routers, schemas, and endpoint handlers.
"""

from api.schemas import BaseResponse, ErrorResponse, PaginatedResponse

__all__ = [
    "BaseResponse",
    "ErrorResponse",
    "PaginatedResponse",
]
