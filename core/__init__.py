# core/__init__.py
"""Core module for AP Automation Engine.

This module contains the foundational components:
- Configuration management via pydantic-settings
- Database session management with async SQLAlchemy
- Security utilities for JWT and password hashing
"""

from core.config import get_settings, Settings
from core.database import (
    get_db_session,
    init_db,
    close_db,
    AsyncSessionLocal,
    engine,
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
    "get_db_session",
    "init_db",
    "close_db",
    "AsyncSessionLocal",
    "engine",
    "create_access_token",
    "verify_password",
    "get_password_hash",
    "decode_token",
]
