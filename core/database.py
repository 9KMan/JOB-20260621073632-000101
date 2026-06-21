# core/database.py
"""Async SQLAlchemy database session management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from core.config import settings

# Create async engine with connection pooling
engine: AsyncEngine = create_async_engine(
    settings.database.database_url,
    echo=settings.database.database_echo,
    pool_size=settings.database.database_pool_size,
    max_overflow=settings.database.database_max_overflow,
    pool_timeout=settings.database.database_pool_timeout,
    pool_pre_ping=True,
    poolclass=NullPool if settings.app.debug else None,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI to get database session.

    Yields:
        AsyncSession: Database session that auto-closes on exit
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database sessions outside of FastAPI.

    Useful for background workers and CLI commands.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Initialize database - create extensions, tables, etc.

    Called during application startup.
    """
    async with engine.begin() as conn:
        # Enable UUID extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"pg_trgm\""))


async def close_db() -> None:
    """Close database connections.

    Called during application shutdown.
    """
    await engine.dispose()


async def health_check() -> bool:
    """Check database connectivity.

    Returns:
        True if database is reachable, False otherwise
    """
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception:
        return False


# Type alias for dependency injection
DbSession = Annotated[AsyncSession, None]

__all__ = [
    "engine",
    "AsyncSessionLocal",
    "get_db_session",
    "get_db_context",
    "init_db",
    "close_db",
    "health_check",
    "DbSession",
]
