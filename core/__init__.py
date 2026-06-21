# core/__init__.py
"""Core module — config, database, security, and main app."""

from core.config import settings
from core.database import get_db, AsyncSessionLocal

__all__ = [
    "settings",
    "get_db",
    "AsyncSessionLocal",
]
