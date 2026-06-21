// api/__init__.py
"""API package for AP Automation Engine.

Exposes the FastAPI application and API routers.
"""

from api.v1.router import api_router

__all__ = ["api_router"]
