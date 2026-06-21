# api/__init__.py
"""API module for AP Automation Engine.

This module contains FastAPI routes and Pydantic schemas.
"""

from api.schemas import HealthResponse

__all__ = ["HealthResponse"]
