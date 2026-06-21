# core/__init__.py
"""Core module for AP Automation Engine.

This module contains configuration, database, and security utilities.
"""

from core.config import get_settings, Settings
from core.database import (
    get_db,
    AsyncSessionLocal,
    init_db,
    close_db,
    EngineManager,
)
from core.security import (
    create_access_token,
    verify_password,
    get_password_hash,
    TokenData,
    CurrentUser,
)

__all__ = [
    "get_settings",
    "Settings",
    "get_db",
    "AsyncSessionLocal",
    "init_db",
    "close_db",
    "EngineManager",
    "create_access_token",
    "verify_password",
    "get_password_hash",
    "TokenData",
    "CurrentUser",
]

__version__ = "0.1.0"
