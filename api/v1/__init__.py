# api/v1/__init__.py
"""API v1 module.

Contains all versioned API endpoints.
"""

from api.v1.router import api_router

__all__ = ["api_router"]
