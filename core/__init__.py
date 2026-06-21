# core/__init__.py
"""
Core package initialization.

This module exposes the core application components including
configuration, database, and security utilities.
"""

from core.config import settings
from core.database import get_db, DatabaseManager

__all__ = [
    "settings",
    "get_db",
    "DatabaseManager",
]
