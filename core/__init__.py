// core/__init__.py
"""
Core package for AP Automation Engine.

This package contains configuration, database, and security utilities.
"""

from core.config import settings
from core.database import get_db_session, engine, async_session_factory

__all__ = [
    "settings",
    "get_db_session",
    "engine",
    "async_session_factory",
]
