# api/__init__.py
"""API package for AP Automation Engine."""

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
