# core/database.py
"""Async SQLAlchemy database session management.

Provides async session factory and dependency injection for FastAPI.
Uses asyncpg driver for PostgreSQL with connection pooling.
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

from core.config import settings

# Create async engine with connection pooling
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    poolclass=AsyncAdaptedQueuePool,
    # SQLAlchemy 2.0 async pool settings
    pool_pre_ping=True,
    connect_args={
        "server_settings": {
            "jit": "off",
            "application_name": settings.APP_NAME,
        },
    },
)

# Async session factory
async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database session injection.

    Yields:
        AsyncSession: An async SQLAlchemy session.

    Example:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db_session)):
            result = await db.execute(select(Item))
            return result.scalars().all()
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
async def get_db_session_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database session (outside of FastAPI request).

    Use this for background tasks, workers, or scripts.

    Yields:
        AsyncSession: An async SQLAlchemy session.

    Example:
        async with get_db_session_context() as session:
            result = await session.execute(select(Invoice))
            invoices = result.scalars().all()
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


# Type alias for dependency injection
DBSession = Annotated[AsyncSession, Depends(get_db_session)]


async def init_db() -> None:
    """Initialize database tables.

    Creates all tables defined in models if they don't exist.
    For production, use Alembic migrations instead.
    """
    from models.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections gracefully.

    Called during application shutdown.
    """
    await engine.dispose()
