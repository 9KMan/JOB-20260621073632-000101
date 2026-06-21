// core/__init__.py
"""Core package for AP Automation Engine.

This package contains the foundational modules:
- config: Environment/settings management via pydantic-settings
- database: Async SQLAlchemy session management
- security: JWT + bcrypt authentication utilities
"""

from core.config import get_settings, Settings
from core.database import (
    get_db,
    get_async_session,
    AsyncSessionLocal,
    async_engine,
    Base,
)
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
    "get_db",
    "get_async_session",
    "AsyncSessionLocal",
    "async_engine",
    "Base",
    "create_access_token",
    "verify_password",
    "get_password_hash",
    "get_current_user",
    "TokenPayload",
]
