# api/__init__.py
"""API package for AP Automation Engine."""

from api.schemas import ErrorResponse, HealthResponse, PaginatedResponse

__all__ = ["ErrorResponse", "HealthResponse", "PaginatedResponse"]
