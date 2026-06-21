# api/v1/__init__.py
"""API v1 package.

Contains all versioned API endpoints for the AP Automation Engine.
"""

from api.v1.router import api_router

__all__ = ["api_router"]
