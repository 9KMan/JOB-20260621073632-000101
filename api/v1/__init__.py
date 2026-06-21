# api/v1/__init__.py
"""API v1 module for AP Automation Engine.

This package contains v1 API routes.
"""

from api.v1.router import api_router

__all__ = ["api_router"]
