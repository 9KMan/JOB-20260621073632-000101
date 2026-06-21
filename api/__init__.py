# api/__init__.py
"""API module for AP Automation Engine.

This module contains API routes, schemas, and routing configuration.
"""

from api.v1.router import api_router

__all__ = ["api_router"]
