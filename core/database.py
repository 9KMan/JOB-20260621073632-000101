# core/database.py
"""Async SQLAlchemy database session management.

Provides async session factory and dependency injection for FastAPI.
"""

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
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool

from core.config import settings


def _engine_kwargs() -> dict[str, Any]:
    """Build engine kwargs based on configuration."""
    kwargs: dict[str, Any] = {
        "echo": settings.DEBUG,
        "pool_size": settings.DATABASE_POOL_SIZE,
        "max_overflow": settings.DATABASE_MAX_OVERFLOW,
        "pool_timeout": settings.DATABASE_POOL_TIMEOUT,
        "pool_recycle": settings.DATABASE_POOL_RECYCLE,
        "pool_pre_ping": True,
    }

    # Use NullPool for PGBouncer (transaction pooling mode)
    if settings.PGBOUNCER_HOST:
        kwargs["poolclass"] = NullPool
        kwargs.pop("pool_size", None)
        kwargs.pop("max_overflow", None)

    return kwargs


# Create async engine
engine: AsyncEngine = create_async_engine(
    settings.effective_database_url,
    **_engine_kwargs(),
)

# Async session factory
async_session_maker: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides a database session.

    Yields:
        AsyncSession: SQLAlchemy async session

    Example:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    async with async_session_maker() as session:
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
    """Context manager for database sessions (for use outside of FastAPI)."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database connection and create tables if needed."""
    from models.base import Base

    async with engine.begin() as conn:
        # Enable UUID extension for PostgreSQL
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""))
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections gracefully."""
    await engine.dispose()


async def check_db_health() -> bool:
    """Check if database connection is healthy.

    Returns:
        bool: True if connection is healthy, False otherwise
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


class DatabaseHelper:
    """Helper class for database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def execute(self, query: Any) -> Any:
        """Execute a query and return results."""
        result = await self.session.execute(query)
        return result

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self.session.commit()

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        await self.session.rollback()

    async def refresh(self, instance: Any) -> None:
        """Refresh an instance from the database."""
        await self.session.refresh(instance)

    async def flush(self) -> None:
        """Flush pending changes to the database."""
        await self.session.flush()
