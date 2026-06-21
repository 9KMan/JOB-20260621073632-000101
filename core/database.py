# core/database.py
"""Async SQLAlchemy database session management.

Provides async database sessions with proper connection pooling,
transaction management, and cleanup handling.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy import create_async_engine, event, exc, pool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from core.config import get_settings

logger = logging.getLogger(__name__)

# Global engine instance - initialized on startup
engine: AsyncEngine | None = None
async_session_factory: async_sessionmaker[AsyncSession] | None = None


async def init_db() -> None:
    """Initialize database engine and session factory.

    Creates the async engine with connection pooling configuration
    and sets up the session factory for dependency injection.
    """
    global engine, async_session_factory

    settings = get_settings()

    # Create async engine with connection pooling
    engine = create_async_engine(
        settings.database_url,
        echo=settings.debug,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_timeout=settings.database_pool_timeout,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

    # Create session factory
    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    logger.info(
        "Database engine initialized",
        extra={
            "pool_size": settings.database_pool_size,
            "max_overflow": settings.database_max_overflow,
        },
    )


async def close_db() -> None:
    """Close database engine and cleanup connections.

    Should be called on application shutdown.
    """
    global engine, async_session_factory

    if engine is not None:
        await engine.dispose()
        engine = None
        async_session_factory = None
        logger.info("Database engine closed")


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session for dependency injection.

    Yields:
        AsyncSession: SQLAlchemy async session

    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db_session)):
            ...
    """
    if async_session_factory is None:
        raise RuntimeError(
            "Database not initialized. Call init_db() first."
        )

    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_db_session_context() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session as context manager.

    For use outside of FastAPI dependency injection.

    Usage:
        async with get_db_session_context() as session:
            result = await session.execute(select(Model))
    """
    if async_session_factory is None:
        raise RuntimeError(
            "Database not initialized. Call init_db() first."
        )

    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_raw_connection() -> Any:
    """Get raw asyncpg connection for advanced operations."""
    if engine is None:
        raise RuntimeError("Database not initialized")

    async with engine.connect() as conn:
        return conn


class AsyncSessionLocal:
    """Async session factory for dependency injection compatibility."""

    def __init__(self) -> None:
        """Initialize session local."""
        self._session_factory = async_session_factory

    async def __call__(self) -> AsyncGenerator[AsyncSession, None]:
        """Call as dependency."""
        if self._session_factory is None:
            raise RuntimeError("Database not initialized")
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


# Create default instance for FastAPI Depends
async def get_db(
    session: AsyncSession = Depends(get_db_session),
) -> AsyncSession:
    """FastAPI dependency for database session.

    Args:
        session: Injected async session

    Returns:
        AsyncSession instance
    """
    return session


# Import Depends at module level to avoid circular imports
from fastapi import Depends
