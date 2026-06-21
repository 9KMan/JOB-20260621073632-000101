# core/database.py
"""Async SQLAlchemy database session management.

This module provides async database session handling using
SQLAlchemy 2.0 async capabilities with proper connection pooling.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from sqlalchemy import event
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
    settings.effective_database_url,
    echo=settings.database_echo,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
    autoflush=False,
)

# Type alias for dependency injection
AsyncSessionDep = Annotated[AsyncSession, None]


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides an async database session.

    Yields:
        AsyncSession: SQLAlchemy async session

    Example:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db_session)):
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
    """Context manager for database sessions.

    Use this for non-FastAPI contexts like workers or scripts.

    Yields:
        AsyncSession: SQLAlchemy async session
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
    """
    from models.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections gracefully."""
    await engine.dispose()
