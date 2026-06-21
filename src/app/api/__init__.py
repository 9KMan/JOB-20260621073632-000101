// src/app/api/__init__.py
"""API routes package."""

from src.app.api.v1 import router as v1_router

__all__ = ["v1_router"]
