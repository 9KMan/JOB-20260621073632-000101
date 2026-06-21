# core/__init__.py
"""
Core module initialization.

This module contains the foundational infrastructure components:
- Configuration management via pydantic-settings
- Database session management for async SQLAlchemy
- Security utilities for JWT and password hashing
"""

from core.config import get_settings, Settings
from core.database import (
    get_db,
    AsyncSessionLocal,
    async_engine,
    sync_engine,
    init_db,
    close_db,
)
from core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_password_hash,
    decode_token,
)

__all__ = [
    # Config
    "get_settings",
    "Settings",
    # Database
    "get_db",
    "AsyncSessionLocal",
    "async_engine",
    "sync_engine",
    "init_db",
    "close_db",
    # Security
    "create_access_token",
    "create_refresh_token",
    "verify_password",
    "get_password_hash",
    "decode_token",
]
