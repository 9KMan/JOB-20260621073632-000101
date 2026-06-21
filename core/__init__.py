# core/__init__.py
"""Core module for AP Automation Engine.

This module contains the foundational components:
- Configuration management via pydantic-settings
- Database session management
- Security utilities (JWT, bcrypt)
"""

__version__ = "0.1.0"

from core.config import settings
from core.database import AsyncSessionLocal, get_db, engine

__all__ = [
    "settings",
    "AsyncSessionLocal",
    "get_db",
    "engine",
]
