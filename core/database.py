// core/database.py
"""Database session management and SQLAlchemy async engine configuration."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from core.config import get_settings


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models.

    All database models should inherit from this class.
    Provides common functionality like soft-delete support.
    """

    pass


def get_async_engine() -> AsyncEngine:
    """Create and configure the async database engine.

    Returns:
        Configured AsyncEngine instance.
    """
    settings = get_settings()

    engine = create_async_engine(
        settings.database_url,
        echo=settings.database_echo,
        **settings.get_database_pool_config(),
    )

    return engine


# Global engine instance
engine = get_async_engine()

# Async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class DatabaseSession:
    """Database session context manager wrapper.

    Provides a simple interface for managing async database sessions.
    Can be used as a context manager or FastAPI dependency.
    """

    def __init__(self) -> None:
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> AsyncSession:
        self._session = async_session_maker()
        return self._session

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._session:
            if exc_type is not None:
                await self._session.rollback()
            await self._session.close()
            self._session = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database session injection.

    Provides an async session that is automatically committed on success
    and rolled back on exception.

    Args:
        Yields:
            AsyncSession: The database session.

    Example:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    async with DatabaseSession() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Type alias for dependency injection
DbSession = Annotated[AsyncSession, Depends(get_db)]


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database session outside of FastAPI.

    Useful for background tasks, scripts, and CLI commands.

    Yields:
        AsyncSession: The database session.
    """
    async with DatabaseSession() as session:
        yield session


async def init_db() -> None:
    """Initialize the database by creating all tables.

    This function creates all tables defined by models inheriting from Base.
    Should be called during application startup.

    Note: In production, use Alembic migrations instead.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
    """Drop all database tables.

    WARNING: This will delete all data. Use with caution.

    Note: In production, use Alembic migrations instead.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def check_db_connection() -> bool:
    """Check if the database connection is healthy.

    Returns:
        True if connection is successful, False otherwise.
    """
    try:
        async with get_db_context() as session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception:
        return False


async def get_db_stats() -> dict[str, Any]:
    """Get database connection pool statistics.

    Returns:
        Dictionary containing pool statistics.
    """
    pool = engine.sync_engine.pool
    return {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "invalid": pool.invalidatedcount() if hasattr(pool, "invalidatedcount") else 0,
    }
