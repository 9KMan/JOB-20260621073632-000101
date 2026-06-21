// core/__init__.py
"""Core module for AP Automation Core Engine.

This module contains the foundational components of the application:
- Configuration management
- Database connection and session management
- Security utilities (JWT, password hashing)

All environment-based configuration is handled through pydantic-settings
to ensure type safety and validation of required environment variables.
"""

from core.config import get_settings, Settings
from core.database import (
    get_db,
    get_async_session,
    init_db,
    close_db,
    AsyncSessionLocal,
    Base,
)
from core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_token,
    get_current_user,
    JWTPayload,
)

__all__ = [
    # Config
    "get_settings",
    "Settings",
    # Database
    "get_db",
    "get_async_session",
    "init_db",
    "close_db",
    "AsyncSessionLocal",
    "Base",
    # Security
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "decode_token",
    "get_current_user",
    "JWTPayload",
]

__version__ = "1.0.0"
