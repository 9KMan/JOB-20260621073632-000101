# core/__init__.py
"""Core package for AP Automation Engine.

This package contains the foundational components:
- Configuration management (pydantic-settings)
- Database session management (SQLAlchemy async)
- Security utilities (JWT, bcrypt)
"""

from core.config import settings
from core.database import get_db, DataBaseManager

__all__ = [
    "settings",
    "get_db",
    "DataBaseManager",
]
