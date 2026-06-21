# api/__init__.py
"""API package for AP Automation Engine."""

from api.schemas import BaseResponse, ErrorResponse, PaginatedResponse

__all__ = ["BaseResponse", "ErrorResponse", "PaginatedResponse"]
