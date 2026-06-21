# api/__init__.py
"""API package for FastAPI endpoints."""

from api.schemas import BaseResponse, ErrorResponse, HealthResponse

__all__ = [
    "BaseResponse",
    "ErrorResponse",
    "HealthResponse",
]
