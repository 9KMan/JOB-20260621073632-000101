// core/database.py
"""Async SQLAlchemy database session management.

This module provides async database session handling using SQLAlchemy 2.0's
async capabilities. It includes connection pooling, session factory setup,
and dependency injection for FastAPI routes.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from typing_extensions import TypeAlias

from core.config import get_settings

logger = logging.getLogger(__name__)

# Naming convention for database constraints
NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
    "雪花": "snowflake_%(table_name)s_%(column_0_label)s",
}

# Create metadata with naming convention
metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base class.

    All database models should inherit from this class.
    It provides common functionality like timestamp handling
    and table naming conventions.
    """

    metadata = metadata


# Type aliases for better code readability
AsyncSessionLocal: TypeAlias = async_sessionmaker[AsyncSession]
DatabaseSession: TypeAlias = AsyncSession


def create_async_engine_from_settings() -> AsyncEngine:
    """Create async engine with settings from config.

    Returns:
        Configured AsyncEngine instance
    """
    settings = get_settings()

    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600,
        connect_args={
            "server_settings": {
                "application_name": "ap_automation",
                "timezone": "UTC",
            },
        },
    )

    logger.info(
        "Database engine created",
        extra={
            "host": settings.DATABASE_URL.split("@")[1].split("/")[0]
            if "@" in settings.DATABASE_URL
            else "unknown"
        },
    )

    return engine


# Global async engine instance
async_engine: AsyncEngine = create_async_engine_from_settings()

# Session factory with autocommit=False for explicit transaction control
async_session_maker: AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
    future=True,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI routes to get database session.

    This function is designed to be used as a FastAPI dependency.
    It ensures proper session lifecycle management including
    cleanup on request completion.

    Args:
        yield: AsyncSession instance for the request

    Yields:
        AsyncSession: Database session for the current request

    Example:
        