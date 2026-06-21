# core/__init__.py
"""Core package initialization.

This module provides the core infrastructure components for the AP Automation Engine:
- Configuration management via pydantic-settings
- Database session management for async SQLAlchemy
- Security utilities for JWT and password hashing
"""

from core.config import get_settings, Settings
from core.database import (
    get_db,
    AsyncSessionLocal,
    async_engine,
    init_db,
    close_db,
)
from core.security import (
    create_access_token,
    verify_password,
    get_password_hash,
    decode_token,
)

__all__ = [
    "get_settings",
    "Settings",
    "get_db",
    "AsyncSessionLocal",
    "async_engine",
    "init_db",
    "close_db",
    "create_access_token",
    "verify_password",
    "get_password_hash",
    "decode_token",
]

__version__ = "1.0.0"
