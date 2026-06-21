# src/api/__init__.py
"""API module for AP Automation Core Engine.

This module contains FastAPI routes, schemas, and API utilities.
"""

from api.v1 import router as v1_router

__all__ = ["v1_router"]
