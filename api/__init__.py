# api/__init__.py
"""API package for AP Automation Engine.

Exposes FastAPI application and router components.
"""

from api.schemas import (
    ErrorResponse,
    HealthCheck,
    PaginatedResponse,
    MessageResponse,
)

__all__ = [
    "ErrorResponse",
    "HealthCheck",
    "PaginatedResponse",
    "MessageResponse",
]
