# core/__init__.py
# Core package initialization
# AP Automation Core Engine — FinaRo

"""Core module for configuration, database, and security.

This module contains the foundational components used across the application:
- Configuration management via pydantic-settings
- Async SQLAlchemy database session handling
- JWT and bcrypt security utilities
"""

from core.config import get_settings, Settings
from core.database import get_db_session, AsyncSessionLocal, engine
from core.security import (
    create_access_token,
    verify_password,
    get_password_hash,
    get_current_user,
    TokenPayload,
)

__all__ = [
    "get_settings",
    "Settings",
    "get_db_session",
    "AsyncSessionLocal",
    "engine",
    "create_access_token",
    "verify_password",
    "get_password_hash",
    "get_current_user",
    "TokenPayload",
]
