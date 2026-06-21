# core/database.py
"""Async SQLAlchemy database session management.

Provides async session factory and dependency injection helpers.
"""

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
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from core.config import get_settings


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""

    pass


# Async engine instance
_async_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None

# Sync engine instance (for migrations and testing)
_sync_engine: Any = None
_sync_session_factory: sessionmaker[Session] | None = None


def get_async_engine() -> AsyncEngine:
    """Get or create async database engine."""
    global _async_engine
    if _async_engine is None:
        settings = get_settings()
        _async_engine = create_async_engine(
            str(settings.database_url),
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_timeout=settings.database_pool_timeout,
            pool_recycle=settings.database_pool_recycle,
            echo=settings.database_echo,
            pool_pre_ping=True,
        )
    return _async_engine


def get_async_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create async session factory."""
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


def get_sync_engine() -> Any:
    """Get or create sync database engine for migrations."""
    global _sync_engine
    if _sync_engine is None:
        settings = get_settings()
        # Convert async URL to sync URL
        sync_url = str(settings.database_url).replace("+asyncpg", "")
        _sync_engine = create_engine(
            sync_url,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_timeout=settings.database_pool_timeout,
            pool_recycle=settings.database_pool_recycle,
            echo=settings.database_echo,
            pool_pre_ping=True,
        )
    return _sync_engine


def get_sync_session_factory() -> sessionmaker[Session]:
    """Get or create sync session factory."""
    global _sync_session_factory
    if _sync_session_factory is None:
        _sync_session_factory = sessionmaker(
            bind=get_sync_engine(),
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return _sync_session_factory


async def init_db() -> None:
    """Initialize database connection and create tables if needed."""
    engine = get_async_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    global _async_engine, _async_session_factory, _sync_engine, _sync_session_factory

    if _async_engine is not None:
        await _async_engine.dispose()
        _async_engine = None
        _async_session_factory = None

    if _sync_engine is not None:
        _sync_engine.dispose()
        _sync_engine = None
        _sync_session_factory = None


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for async database session.

    Yields:
        AsyncSession: SQLAlchemy async session

    Example:
        @app.post("/items")
        async def create_item(session: AsyncSession = Depends(get_session)):
            item = Item(name="test")
            session.add(item)
            await session.commit()
    """
    factory = get_async_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_session_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database session (non-FastAPI usage).

    Yields:
        AsyncSession: SQLAlchemy async session

    Example:
        async with get_session_context() as session:
            result = await session.execute(select(Item))
            items = result.scalars().all()
    """
    factory = get_async_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_raw_connection() -> AsyncGenerator[Any, None]:
    """Get raw asyncpg connection for advanced operations."""
    engine = get_async_engine()
    async with engine.connect() as conn:
        yield conn


async def check_database_health() -> dict[str, Any]:
    """Check database connectivity and health.

    Returns:
        dict: Health status including connection info
    """
    try:
        engine = get_async_engine()
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1 AS health_check"))
            row = result.fetchone()
            return {
                "status": "healthy" if row and row[0] == 1 else "unhealthy",
                "database_url": str(get_settings().database_url).split("@")[-1]
                if "@" in str(get_settings().database_url)
                else "configured",
            }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


# Alias for backward compatibility
async_session_factory = get_async_session_factory
