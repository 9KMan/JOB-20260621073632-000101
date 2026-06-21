# core/__init__.py
"""Core module for AP Automation Engine.

This module contains the core configuration, database, and security
components that are shared across the entire application.
"""

__version__ = "0.1.0"

from core.config import settings

__all__ = ["settings"]
