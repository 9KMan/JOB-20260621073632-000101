# core/database.py
"""Async SQLAlchemy database session management.

Provides async database engine, session factory, and session management utilities.
Optimized for PostgreSQL with connection pooling.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool

from core.config import get_settings


def create_async_engine_with_pool() -> AsyncEngine:
    """Create async engine with configured connection pooling.

    Returns:
        AsyncEngine: Configured SQLAlchemy async engine
    """
    settings = get_settings()
    db_settings = settings.database

    return create_async_engine(
        db_settings.database_url,
        pool_size=db_settings.database_pool_size,
        max_overflow=db_settings.database_max_overflow,
        pool_timeout=db_settings.database_pool_timeout,
        pool_recycle=db_settings.database_pool_recycle,
        poolclass=AsyncAdaptedQueuePool,
        echo=db_settings.database_echo,
        future=True,
    )


# Global async engine instance
async_engine: AsyncEngine = create_async_engine_with_pool()

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
    future=True,
)


async def init_db() -> None:
    """Initialize database connection and create tables.

    Should be called on application startup.
    """
    from models.base import Base

    async with async_engine.begin() as conn:
        # Create all tables if they don't exist
        # In production, use Alembic migrations instead
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections.

    Should be called on application shutdown.
    """
    await async_engine.dispose()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database session.

    Yields:
        AsyncSession: Database session for request handling

    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database session.

    Alternative to dependency injection for use in background tasks.

    Yields:
        AsyncSession: Database session

    Usage:
        async with get_db_context() as db:
            result = await db.execute(select(Invoice))
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_session() -> AsyncSession:
    """Get a new database session.

    Caller is responsible for committing/rolling back and closing.

    Returns:
        AsyncSession: New database session
    """
    return AsyncSessionLocal()


class DatabaseManager:
    """Database manager for controlling connection lifecycle."""

    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None

    async def initialize(self) -> None:
        """Initialize database connections."""
        await init_db()

    async def shutdown(self) -> None:
        """Shutdown database connections."""
        await close_db()

    @property
    def engine(self) -> AsyncEngine:
        """Get database engine."""
        if self._engine is None:
            self._engine = create_async_engine_with_pool()
        return self._engine

    async def get_session(self) -> AsyncSession:
        """Get a new session."""
        return AsyncSessionLocal()


# Global database manager instance
db_manager = DatabaseManager()
