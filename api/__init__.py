# api/__init__.py
"""API module for the AP Automation Engine.

This module contains:
- Shared Pydantic schemas
- Versioned API routers
- API utilities and helpers
"""

from api.v1.router import api_router

__all__ = ["api_router"]
