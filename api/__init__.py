// api/__init__.py
"""API package for AP Automation Engine.

This package contains FastAPI routers and Pydantic schemas for the REST API.
"""

from api.schemas import HealthCheck

__all__ = [
    "HealthCheck",
]
