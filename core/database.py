# core/database.py
"""Async SQLAlchemy session management with connection pooling."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool

from core.config import settings

# Build async engine with connection pooling
_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Get or create the async database engine singleton."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.database.url,
            pool_size=settings.database.pool_size,
            max_overflow=settings.database.max_overflow,
            pool_timeout=settings.database.pool_timeout,
            pool_recycle=settings.database.pool_recycle,
            pool_class=AsyncAdaptedQueuePool,
            echo=settings.database.echo,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create the async session factory singleton."""
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return _async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a managed async SQLAlchemy session.

    Yields:
        An AsyncSession scoped to the request.
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for obtaining an async session outside of FastAPI.

    Yields:
        An AsyncSession scoped to the context.
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Initialize database — create all tables via metadata.

    Note: In production use Alembic migrations instead.
    """
    from models.base import Base

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close the database engine and release all connections."""
    global _engine, _async_session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_factory = None
