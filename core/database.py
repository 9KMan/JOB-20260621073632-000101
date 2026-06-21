// core/database.py
"""Async SQLAlchemy database session management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, QueuePool

from core.config import settings


def get_engine_kwargs() -> dict[str, Any]:
    """Get engine kwargs based on environment."""
    kwargs: dict[str, Any] = {
        "echo": settings.debug,
        "future": True,
        "pool_pre_ping": True,
    }

    if settings.debug:
        kwargs["poolclass"] = NullPool
    else:
        kwargs["poolclass"] = QueuePool
        kwargs["pool_size"] = 20
        kwargs["max_overflow"] = 10
        kwargs["pool_recycle"] = 3600
        kwargs["pool_timeout"] = 30

    return kwargs


# Create async engine
engine: AsyncEngine = create_async_engine(
    settings.database_async_url,
    **get_engine_kwargs(),
)

# Async session factory
async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields a database session.

    Yields:
        AsyncSession: Database session that auto-closes after use.
    """
    async with async_session_factory() as session:
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
    """Context manager for database session (for use outside of FastAPI dependencies).

    Yields:
        AsyncSession: Database session that auto-closes after use.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_raw_connection() -> Any:
    """Get a raw asyncpg connection for advanced operations."""
    async with engine.connect() as conn:
        yield conn


async def check_database_connection() -> bool:
    """Check if database connection is healthy.

    Returns:
        True if connection is healthy, False otherwise.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def init_database() -> None:
    """Initialize database (create extensions, etc)."""
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS 'uuid-ossp'"))


async def close_database() -> None:
    """Close database connections."""
    await engine.dispose()


class DatabaseManager:
    """Manager for database operations."""

    def __init__(self) -> None:
        self.engine = engine
        self.session_factory = async_session_factory

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session context manager.

        Yields:
            AsyncSession: Database session.
        """
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def execute(self, query: str, params: dict[str, Any] | None = None) -> Any:
        """Execute a raw SQL query.

        Args:
            query: SQL query string.
            params: Query parameters.

        Returns:
            Query result.
        """
        async with self.session() as session:
            result = await session.execute(text(query), params or {})
            return result

    async def scalar(self, query: str, params: dict[str, Any] | None = None) -> Any:
        """Execute a query and return a scalar value.

        Args:
            query: SQL query string.
            params: Query parameters.

        Returns:
            Scalar result.
        """
        result = await self.execute(query, params)
        return result.scalar()


# Global database manager instance
db_manager = DatabaseManager()
