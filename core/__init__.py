# core/__init__.py
"""Core package for AP Automation Core Engine.

This package contains the foundational components:
- config: Environment settings via pydantic-settings
- database: Async SQLAlchemy session management
- security: JWT and bcrypt utilities
- main: FastAPI application factory
"""

__version__ = "0.1.0"

from core.config import settings
from core.database import get_db_session, AsyncSessionLocal, engine

__all__ = [
    "settings",
    "get_db_session",
    "AsyncSessionLocal",
    "engine",
]
