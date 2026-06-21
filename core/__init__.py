# core/__init__.py
"""
AP Automation Core Engine — Core Module

This module contains configuration, database, and security utilities
for the FinaRo AP Automation system.
"""

__version__ = "0.1.0"
__all__ = [
    "config",
    "database",
    "security",
    "exceptions",
]

from core.config import settings
from core.database import (
    AsyncSessionLocal,
    async_engine,
    async_session_factory,
    get_db,
)
from core.security import (
    create_access_token,
    verify_password,
    get_password_hash,
    get_current_user,
    JWTPayload,
)

__all__ = [
    "__version__",
    "settings",
    "AsyncSessionLocal",
    "async_engine",
    "async_session_factory",
    "get_db",
    "create_access_token",
    "verify_password",
    "get_password_hash",
    "get_current_user",
    "JWTPayload",
]
