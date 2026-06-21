// src/app/core/logging.py
"""
Logging configuration for the application.
"""
import logging
import sys
from typing import Any, Dict


def setup_logging() -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Set SQLAlchemy logging level
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    # Set Alembic logging
    logging.getLogger("alembic").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


class StructuredLogger:
    """Structured logger for JSON logging in production."""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def _log(
        self, level: int, message: str, extra: Dict[str, Any] = None
    ) -> None:
        """Log with structured data."""
        extra = extra or {}
        self.logger.log(level, message, extra=extra)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info level message."""
        self._log(logging.INFO, message, kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning level message."""
        self._log(logging.WARNING, message, kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error level message."""
        self._log(logging.ERROR, message, kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug level message."""
        self._log(logging.DEBUG, message, kwargs)
