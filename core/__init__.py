# core/__init__.py
"""Core module for AP Automation Engine.

This module contains the foundational infrastructure components:
- Configuration management via pydantic-settings
- Database session management with async SQLAlchemy
- Security utilities for JWT and password hashing
"""

from core.config import settings
from core.database import (
    Base,
    DatabaseSession,
    get_db,
    get_async_session,
    engine,
    async_engine,
)

__all__ = [
    "settings",
    "Base",
    "DatabaseSession",
    "get_db",
    "get_async_session",
    "engine",
    "async_engine",
]
