// core/database.py
"""Async SQLAlchemy database session management.

Provides async session factory and dependency injection for FastAPI.
Connection pooling is handled by SQLAlchemy async engine.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, QueuePool

from core.config import get_settings


def _get_engine_config() -> dict:
    """Build SQLAlchemy async engine configuration from settings."""
    settings = get_settings()

    # Use PGBouncer if configured, otherwise direct PostgreSQL
    if settings.pgbouncer_host:
        database_url = (
            f"postgresql+asyncpg://{settings.database_url.split('@')[-1].split('/')[0].split(':')[0].split('@')[0]}:"
            f"{settings.database_url.split(':')[2].split('@')[0]}@"
            f"{settings.pgbouncer_host}:{settings.pgbouncer_port}/"
            f"{settings.database_url.split('/')[-1]}"
        )
    else:
        database_url = settings.database_url

    return {
        "url": database_url,
        "echo": settings.debug,
        "poolclass": QueuePool,
        "pool_size": 20,
        "max_overflow": 10,
        "pool_pre_ping": True,
        "pool_recycle": 3600,
        "connect_args": {
            "server_settings": {
                "application_name": "ap-automation-engine",
                "jit": "off",
            },
            "timeout": 30,
        },
    }


# Create async engine with configuration
engine: AsyncEngine = create_async_engine(**_get_engine_config())

# Session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def init_db() -> None:
    """Initialize database connection and create tables if needed.

    Called during application startup.
    """
    settings = get_settings()

    # Test connection
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))

    # Enable UUID extension if not already enabled
    async with engine.begin() as conn:
        await conn.execute(
            text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\" CASCADE")
        )


async def close_db() -> None:
    """Close database connections gracefully.

    Called during application shutdown.
    """
    await engine.dispose()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides an async database session.

    Yields:
        AsyncSession: SQLAlchemy async session scoped to the request.

    Example:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db_session)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_db_session_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database sessions outside of FastAPI requests.

    Useful for background tasks and scripts.

    Yields:
        AsyncSession: SQLAlchemy async session.

    Example:
        async with get_db_session_context() as session:
            result = await session.execute(select(Invoice))
            invoices = result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Type alias for dependency injection
DbSession = Annotated[AsyncSession, Depends(get_db_session)]
