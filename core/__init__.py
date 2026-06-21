# core/__init__.py
"""Core module for AP Automation Engine.

This module contains the foundational components:
- Configuration management (pydantic-settings)
- Database session management (SQLAlchemy async)
- Security utilities (JWT, bcrypt)
"""

from core.config import get_settings, Settings
from core.database import (
    get_db_session,
    AsyncSessionLocal,
    init_db,
    close_db,
    engine,
)
from core.security import (
    create_access_token,
    verify_password,
    get_password_hash,
    decode_token,
    get_current_user,
    TokenPayload,
)

__all__ = [
    # Config
    "Settings",
    "get_settings",
    # Database
    "get_db_session",
    "AsyncSessionLocal",
    "init_db",
    "close_db",
    "engine",
    # Security
    "create_access_token",
    "verify_password",
    "get_password_hash",
    "decode_token",
    "get_current_user",
    "TokenPayload",
]
