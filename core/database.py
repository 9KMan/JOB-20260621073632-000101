# core/database.py
"""Async SQLAlchemy database session management.

Provides async session factory and dependency injection for FastAPI.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase

from core.config import settings


# Async engine for API operations
engine = create_async_engine(
    settings.DATABASE_URL,
    poolclass=AsyncAdaptedQueuePool,
    **settings.database_pool_config,
)

# Async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Sync engine for Alembic migrations
sync_engine = create_engine(
    settings.DATABASE_URL_SYNC,
    poolclass=NullPool,
    echo=settings.DATABASE_ECHO,
)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""

    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for async database sessions.

    Yields:
        AsyncSession: SQLAlchemy async session

    Example:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
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
    """Context manager for database sessions outside of FastAPI.

    Yields:
        AsyncSession: SQLAlchemy async session

    Example:
        async with get_db_context() as session:
            result = await session.execute(select(Invoice))
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


async def init_db() -> None:
    """Initialize database tables.

    Creates all tables defined in models.
    Should only be used in development/testing.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections gracefully."""
    await engine.dispose()


# Type aliases for dependency injection
DbSession = Annotated[AsyncSession, Depends(get_db)]
