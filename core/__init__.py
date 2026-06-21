# core/__init__.py
"""Core module for AP Automation Engine.

This module contains the foundational components:
- Configuration management
- Database session management
- Security utilities (JWT, bcrypt)
"""

__version__ = "0.1.0"
__author__ = "FinaRo"

from core.config import settings
from core.database import get_db, engine, async_session_maker

__all__ = [
    "settings",
    "get_db",
    "engine",
    "async_session_maker",
]
