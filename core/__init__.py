// core/__init__.py
"""AP Automation Core Engine - Core Module

This module contains the core application configuration, database management,
and security utilities for the AP Automation system.

Exports:
    - get_settings: Get application settings singleton
    - get_db: Async database session dependency
    - create_app: FastAPI application factory
"""

__version__ = "0.1.0"

from core.config import get_settings, Settings
from core.database import get_db, AsyncSessionLocal, engine, init_db
from core.main import app

__all__ = [
    "get_settings",
    "Settings",
    "get_db",
    "AsyncSessionLocal",
    "engine",
    "init_db",
    "app",
]
