# core/__init__.py
"""Core module for AP Automation Engine.

This module contains the foundational components:
- Configuration management
- Database session handling
- Security utilities (JWT, password hashing)
"""

from core.config import settings
from core.database import get_db_session, engine, async_session_factory

__all__ = [
    "settings",
    "get_db_session",
    "engine",
    "async_session_factory",
]
