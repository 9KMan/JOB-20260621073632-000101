# core/database.py
# Async SQLAlchemy database session management
# AP Automation Core Engine — FinaRo

"""Async SQLAlchemy database session management.

This module provides async database session handling using SQLAlchemy 2.0
with asyncpg driver for PostgreSQL.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool
from sqlalchemy import event

from core.config import get_settings


# Create async engine based on settings
settings = get_settings()

# Configure async engine with connection pooling
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    pool_pre_ping=True,  # Enable connection health checks
    poolclass=AsyncAdaptedQueuePool,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session as a FastAPI dependency.

    This dependency creates a new session for each request and ensures
    proper cleanup after the request completes.

    Yields:
        AsyncSession: The async database session.

    Example:
        