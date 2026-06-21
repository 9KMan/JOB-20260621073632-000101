// core/__init__.py
"""Core module for AP Automation Core Engine.

This module contains configuration, database, and security utilities.
"""

__version__ = "0.1.0"

from core.config import settings
from core.database import get_db, init_db

__all__ = [
    "settings",
    "get_db",
    "init_db",
]
