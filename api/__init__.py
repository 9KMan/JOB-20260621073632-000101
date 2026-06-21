// api/__init__.py
"""API package initialization.

This module provides FastAPI API initialization and exports
the main API router.
"""

from fastapi import APIRouter

from api.v1.router import api_router

__all__ = ["api_router"]
