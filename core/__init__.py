// core/__init__.py
"""Core module for AP Automation Engine.

This module contains the foundational components for the application:
- Configuration management via pydantic-settings
- Database session management
- Security utilities (JWT, bcrypt)
"""

from core.config import settings
from core.database import Base, get_db, engine, async_session_maker

__all__ = [
    "settings",
    "Base",
    "get_db",
    "engine",
    "async_session_maker",
]
