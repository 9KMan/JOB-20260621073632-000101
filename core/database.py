# core/database.py
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


def create_engine() -> AsyncEngine:
    """Create async SQLAlchemy engine with appropriate pool settings.

    In production with PGBouncer, use NullPool to let PGBouncer handle pooling.
    In development, use QueuePool for better connection management.
    """
    engine_kwargs: dict[str, Any] = {
        "echo": settings.debug,
        "future": True,
        "pool_pre_ping": True,
    }

    if settings.environment == "production":
        # In production, use PGBouncer which handles connection pooling
        engine_kwargs["poolclass"] = NullPool
    else:
        # In development, use QueuePool for connection reuse
        engine_kwargs["poolclass"] = QueuePool
        engine_kwargs["pool_size"] = 10
        engine_kwargs["max_overflow"] = 20
        engine_kwargs["pool_recycle"] = 3600  # Recycle connections after 1 hour

    return create_async_engine(
        settings.database_url,
        **engine_kwargs,
    )


# Create engine instance
engine = create_engine()

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI to get async database session.

    Yields:
        AsyncSession: SQLAlchemy async session

    Example:
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
    """Context manager for database session outside of FastAPI dependency injection.

    Yields:
        AsyncSession: SQLAlchemy async session

    Example:
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


async def init_db() -> None:
    """Initialize database - create all tables.

    Note: In production, use Alembic migrations instead.
    This is primarily for development/testing.
    """
    from models.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
    """Drop all database tables.

    Warning: This will delete all data. Use with caution.
    """
    from models.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def check_db_connection() -> bool:
    """Check database connectivity.

    Returns:
        bool: True if connection is healthy
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def get_db_version() -> str | None:
    """Get PostgreSQL server version.

    Returns:
        str: PostgreSQL version string or None if unavailable
    """
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version()"))
            row = result.fetchone()
            if row:
                return str(row[0])
    except Exception:
        pass
    return None
