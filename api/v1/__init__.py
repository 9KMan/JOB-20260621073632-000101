// api/v1/__init__.py
"""API v1 package.

Contains versioned API routes for the application.
"""

from api.v1.router import api_router

__all__ = ["api_router"]
