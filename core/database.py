# core/database.py
"""Async SQLAlchemy session management with connection pooling."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    async_scoped_session,
)
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from typing_extensions import TypeVar

from core.config import settings

# ─────────────────────────────────────────────────────────────────────────────
# Async Engine & Session Factory
# ─────────────────────────────────────────────────────────────────────────────

_async_engine_kwargs = {
    "echo": settings.database.echo,
    "pool_size": settings.database.pool_size,
    "max_overflow": settings.database.max_overflow,
    "pool_timeout": settings.database.pool_timeout,
    "pool_recycle": settings.database.pool_recycle,
    "pool_pre_ping": settings.database.pool_pre_ping,
    "future": True,
}

async_engine: AsyncEngine = create_async_engine(
    str(settings.database.url),
    **_async_engine_kwargs,
)

AsyncSessionFactory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# ─────────────────────────────────────────────────────────────────────────────
# Sync Engine (used by Alembic migrations only)
# ─────────────────────────────────────────────────────────────────────────────

sync_engine = create_engine(
    str(settings.database.url_sync),
    echo=settings.database.echo,
    pool_pre_ping=settings.database.pool_pre_ping,
    pool_size=settings.database.pool_size,
    max_overflow=settings.database.max_overflow,
    pool_recycle=settings.database.pool_recycle,
)

SyncSessionFactory = sessionmaker(
    bind=sync_engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI Dependency
# ─────────────────────────────────────────────────────────────────────────────

_T = TypeVar("_T")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an async database session.

    Automatically handles:
    - Session creation and cleanup
    - Commit on success / rollback on exception
    - Return to the pool
    """
    session: AsyncSession = AsyncSessionFactory()
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
    """
    Context manager version of get_db for use outside of FastAPI routes.
    """
    session: AsyncSession = AsyncSessionFactory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def dispose_engine() -> None:
    """Dispose the async engine and close all connections."""
    await async_engine.dispose()


# ─────────────────────────────────────────────────────────────────────────────
# Utility helpers
# ─────────────────────────────────────────────────────────────────────────────

async def health_check() -> bool:
    """Return True if the database connection is healthy."""
    try:
        async with AsyncSessionFactory() as session:
            await session.execute("SELECT 1")
        return True
    except Exception:
        return False
