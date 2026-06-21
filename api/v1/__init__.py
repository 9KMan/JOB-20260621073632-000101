// api/v1/__init__.py
"""API v1 package.

Contains all versioned API endpoints under /api/v1/.
"""

from api.v1.router import api_router

__all__ = ["api_router"]
