// core/__init__.py
"""Core package for AP Automation Engine.

This package contains configuration, database, and security utilities
that are shared across the application.
"""

from core.config import settings
from core.database import get_db, DatabaseManager

__all__ = [
    "settings",
    "get_db",
    "DatabaseManager",
]
