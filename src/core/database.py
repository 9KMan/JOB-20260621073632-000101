# src/core/database.py
"""Async SQLAlchemy database session management.

Provides async engine, session factory, and dependency injection for FastAPI.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from core.config import settings
from models.base import Base

# Create async engine with connection pooling
async_engine: AsyncEngine = create_async_engine(
    settings.database.database_url,
    echo=settings.app.debug,
    pool_size=settings.database.database_pool_size,
    max_overflow=settings.database.database_max_overflow,
    pool_timeout=settings.database.database_pool_timeout,
    pool_recycle=settings.database.database_pool_recycle,
    pool_pre_ping=True,
)

# Async session factory
async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI to get async database session.

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


async def get_db_without_commit() -> AsyncGenerator[AsyncSession, None]:
    """Alternative dependency when manual commit control is needed.

    Yields:
        AsyncSession: Database session without auto-commit.
    """
    async with async_session_factory() as session:
        yield session


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database sessions outside of FastAPI routes.

    Yields:
        AsyncSession: Database session with automatic commit/rollback.
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


async def init_db() -> None:
    """Initialize database tables.

    Creates all tables defined in models if they don't exist.
    This is primarily for development; use Alembic for production.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
    """Drop all database tables.

    WARNING: This will delete all data. Use only in development/testing.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def close_db() -> None:
    """Close database engine and all connections.

    Call this on application shutdown.
    """
    await async_engine.dispose()


class DatabaseHelper:
    """Helper class for database operations."""

    def __init__(self) -> None:
        self.engine = async_engine
        self.session_factory = async_session_factory

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Context manager for database sessions."""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def create_tables(self) -> None:
        """Create all tables."""
        await init_db()

    async def drop_tables(self) -> None:
        """Drop all tables."""
        await drop_db()


# Singleton instance for convenience
db_helper = DatabaseHelper()


# SQLAlchemy Base class is imported from models.base for convenience
class Base:
    """Placeholder for Base class - import from models.base instead."""

    pass
