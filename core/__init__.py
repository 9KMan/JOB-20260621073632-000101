# core/__init__.py
"""Core module for AP Automation.

This module contains the foundational infrastructure:
- Configuration management via pydantic-settings
- Database session management via SQLAlchemy async
- Security utilities for JWT and password hashing
"""

from core.config import settings
from core.database import get_db, AsyncSessionLocal, engine

__all__ = [
    "settings",
    "get_db",
    "AsyncSessionLocal",
    "engine",
]
