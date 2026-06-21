// src/app/core/logging.py
"""
Structured Logging Configuration
Uses structlog for consistent, machine-readable logging.
"""
import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor

from app.core.config import settings


def setup_logging() -> None:
    """Configure structured logging for the application."""
    # Determine log level
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    
    # Shared processors for all environments
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]
    
    if settings.ENVIRONMENT == "production":
        # Production: JSON output
        shared_processors.extend([
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ])
    else:
        # Development: Colored console output
        shared_processors.extend([
            structlog.dev.ConsoleRenderer(colors=True),
        ])
    
    # Configure structlog
    structlog.configure(
        processors=shared_processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )
    
    # Set third-party loggers to WARNING
    for logger_name in ["uvicorn", "uvicorn.access", "sqlalchemy.engine", "alembic"]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> Any:
    """Get a structured logger instance."""
    return structlog.get_logger(name)
