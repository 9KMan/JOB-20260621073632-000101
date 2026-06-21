// core/__init__.py
"""
Core package for AP Automation Engine.

This package contains the foundational infrastructure:
- Configuration management via pydantic-settings
- Database session management with async SQLAlchemy
- Security utilities for JWT and password hashing
"""

from core.config import settings
from core.database import (
    AsyncSessionLocal,
    async_engine,
    get_db,
    init_db,
    dispose_engine,
)

__all__ = [
    "settings",
    "async_engine",
    "AsyncSessionLocal",
    "get_db",
    "init_db",
    "dispose_engine",
]
