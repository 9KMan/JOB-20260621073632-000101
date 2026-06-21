// api/__init__.py
"""API package initialization.

This module exports the API router and schemas for version 1.
"""

from api.v1.router import api_router

__all__ = ["api_router"]
