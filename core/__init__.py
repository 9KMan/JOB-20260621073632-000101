// core/__init__.py
"""Core package for AP Automation Engine.

This package contains the foundational components:
- Configuration management (config.py)
- Database session management (database.py)
- Security utilities (security.py)
"""

__version__ = "1.0.0"

from core.config import settings
from core.database import get_db_session, AsyncSessionLocal, engine

__all__ = [
    "settings",
    "get_db_session",
    "AsyncSessionLocal",
    "engine",
]
