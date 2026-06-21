# core/__init__.py
"""Core module for AP Automation Engine.

This module contains the core configuration, database, and security
components that are used throughout the application.
"""

from core.config import settings
from core.database import get_db_session, AsyncSessionLocal, engine

__all__ = [
    "settings",
    "get_db_session",
    "AsyncSessionLocal",
    "engine",
]
