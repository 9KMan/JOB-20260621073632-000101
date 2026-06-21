// app/__init__.py
"""FinaRo AP Automation Core Engine"""

__version__ = "1.0.0"
__author__ = "FinaRo Team"

from app.config import settings
from app.database import engine, get_db, AsyncSessionLocal

__all__ = ["settings", "engine", "get_db", "AsyncSessionLocal"]
