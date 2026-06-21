# core/database.py
"""
Async SQLAlchemy database session management.

Provides async database sessions and engine management
for the application with proper connection pooling and lifecycle handling.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool

from core.config import get_settings

logger = logging.getLogger(__name__)

# Global engine instances
_async_engine: AsyncEngine | None = None
_sync_engine: Any = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None
_sync_session_factory: sessionmaker[Session] | None = None


def get_async_engine() -> AsyncEngine:
    """
    Get or create the async database engine.
    
    Returns:
        AsyncEngine: The async SQLAlchemy engine instance.
    """
    global _async_engine
    if _async_engine is None:
        settings = get_settings()
        _async_engine = create_async_engine(
            settings.database.url,
            pool_size=settings.database.pool_size,
            max_overflow=settings.database.max_overflow,
            pool_timeout=settings.database.pool_timeout,
            pool_recycle=settings.database.pool_recycle,
            pool_pre_ping=True,
            echo=settings.database.echo,
        )
        logger.info(
            "Async database engine created",
            extra={
                "url_host": settings.database.url.split("@")[-1] if "@" in settings.database.url else "unknown"
            },
        )
    return _async_engine


def get_sync_engine() -> Any:
    """
    Get or create the sync database engine (for Alembic migrations).
    
    Returns:
        Engine: The sync SQLAlchemy engine instance.
    """
    global _sync_engine
    if _sync_engine is None:
        settings = get_settings()
        _sync_engine = create_engine(
            settings.database.sync_url,
            poolclass=QueuePool,
            pool_size=settings.database.pool_size,
            max_overflow=settings.database.max_overflow,
            pool_timeout=settings.database.pool_timeout,
            pool_recycle=settings.database.pool_recycle,
            pool_pre_ping=True,
            echo=settings.database.echo,
        )
        logger.info("Sync database engine created for migrations")
    return _sync_engine


# Expose engines for direct access
@property
def async_engine() -> AsyncEngine:
    """Property alias for async engine."""
    return get_async_engine()


@property
def sync_engine() -> Any:
    """Property alias for sync engine."""
    return get_sync_engine()


def get_async_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Get or create the async session factory.
    
    Returns:
        async_sessionmaker: The async session factory.
    """
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            bind=get_async_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return _async_session_factory


def get_sync_session_factory() -> sessionmaker[Session]:
    """
    Get or create the sync session factory (for Alembic migrations).
    
    Returns:
        sessionmaker: The sync session factory.
    """
    global _sync_session_factory
    if _sync_session_factory is None:
        _sync_session_factory = sessionmaker(
            bind=get_sync_engine(),
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return _sync_session_factory


# Alias for convenience
AsyncSessionLocal = get_async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides an async database session.
    
    This is the primary way to get database sessions in route handlers.
    The session is automatically closed when the request completes.
    
    Yields:
        AsyncSession: The async database session.
    """
    factory = get_async_session_factory()
    async with factory() as session:
        try:
            yield session
        except Exception as e:
            logger.error(
                "Database session error",
                extra={"error": str(e)},
                exc_info=True,
            )
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions outside of request handlers.
    
    Useful for background tasks, CLI commands, and other non-request contexts.
    
    Yields:
        AsyncSession: The async database session.
    """
    factory = get_async_session_factory()
    async with factory() as session:
        try:
            yield session
        except Exception as e:
            logger.error(
                "Database session error in context manager",
                extra={"error": str(e)},
                exc_info=True,
            )
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize the database by creating all tables.
    
    This is primarily used for development and testing.
    In production, use Alembic migrations.
    """
    from models.base import Base
    
    engine = get_async_engine()
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database tables created")


async def close_db() -> None:
    """
    Close all database connections and dispose of the engine.
    
    Call this during application shutdown.
    """
    global _async_engine, _sync_engine, _async_session_factory, _sync_session_factory
    
    if _async_engine is not None:
        await _async_engine.dispose()
        _async_engine = None
        logger.info("Async database engine disposed")
    
    if _sync_engine is not None:
        _sync_engine.dispose()
        _sync_engine = None
        logger.info("Sync database engine disposed")
    
    _async_session_factory = None
    _sync_session_factory = None


async def check_db_connection() -> bool:
    """
    Check if the database connection is healthy.
    
    Returns:
        bool: True if connection is healthy, False otherwise.
    """
    try:
        engine = get_async_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


async def get_db_version() -> str | None:
    """
    Get the PostgreSQL server version.
    
    Returns:
        str: The PostgreSQL version string, or None if unavailable.
    """
    try:
        engine = get_async_engine()
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version()"))
            row = result.fetchone()
            if row:
                return str(row[0])
        return None
    except Exception as e:
        logger.error(f"Failed to get database version: {e}")
        return None
