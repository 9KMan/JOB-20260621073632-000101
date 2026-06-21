# api/__init__.py
"""API package — FastAPI router, schemas, and endpoints."""

from api.v1.router import api_router

__all__ = ["api_router"]
