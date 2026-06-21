// core/__init__.py
"""Core module for AP Automation Engine.

This module contains shared configuration, database connections,
and security utilities used across the application.
"""

from core.config import settings
from core.database import get_db, AsyncSessionLocal, engine

__all__ = [
    "settings",
    "get_db",
    "AsyncSessionLocal",
    "engine",
]
