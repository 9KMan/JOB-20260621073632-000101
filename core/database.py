// core/database.py
"""Async SQLAlchemy database session management.

This module provides async database session handling with proper
connection pooling and lifecycle management.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool

from core.config import settings


class Base(DeclarativeBase):
    """SQLAlchemy declarative base class."""

    pass


# Async engine configuration
async_engine = create_async_engine(
    settings.database.async_url,
    pool_size=settings.database.pool_size,
    max_overflow=settings.database.max_overflow,
    pool_timeout=settings.database.pool_timeout,
    pool_recycle=settings.database.pool_recycle,
    pool_pre_ping=True,
    echo=settings.app.debug,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Sync engine for migrations and scripts
sync_engine = create_engine(
    settings.database.sync_url,
    poolclass=NullPool,
    echo=settings.app.debug,
)

# Sync session factory for migrations
SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)

# Legacy exports for compatibility
engine: AsyncEngine = async_engine


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session.

    This dependency can be used with FastAPI's Depends() to inject
    database sessions into route handlers.

    Args:
        AsyncSession: The async SQLAlchemy session type.

    Yields:
        AsyncSession: Database session for the request.

    Example:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
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
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session as context manager.

    This is an alternative to get_db() for use outside of FastAPI
    dependency injection, such as in background workers or scripts.

    Yields:
        AsyncSession: Database session.

    Example:
        async with get_db_context() as db:
            result = await db.execute(select(Item))
            items = result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        async with session.begin():
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


async def init_db() -> None:
    """Initialize database tables.

    Creates all tables defined in the models if they don't exist.
    Note: Use Alembic migrations for production database schema management.
    """
    from models.base import Base

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections.

    Should be called during application shutdown.
    """
    await async_engine.dispose()
