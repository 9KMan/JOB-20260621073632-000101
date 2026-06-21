// core/database.py
"""Async SQLAlchemy database session management."""

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

# Create async engine with connection pooling
_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Get or create the async database engine."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create the async session factory."""
    global _async_session_factory
    if _async_session_factory is None:
        engine = get_engine()
        _async_session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return _async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides an async database session.

    Yields:
        AsyncSession: SQLAlchemy async session.
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
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
    """Context manager for database session.

    Yields:
        AsyncSession: SQLAlchemy async session.
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database engine and create tables."""
    engine = get_engine()
    async with engine.begin() as conn:
        # Import all models to ensure they are registered
        from models import __all__ as models  # noqa: F401
        from models.base import Base

        # Create all tables (for development only)
        # In production, use Alembic migrations
        if settings.environment == "development":
            await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database engine and dispose connections."""
    global _engine, _async_session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_factory = None


async def get_raw_connection():
    """Get raw asyncpg connection for advanced operations."""
    engine = get_engine()
    async with engine.connect() as conn:
        yield conn


class DatabaseHelper:
    """Helper class for database operations."""

    @staticmethod
    async def execute_raw(sql: str, params: dict | None = None) -> None:
        """Execute raw SQL statement."""
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text(sql), params or {})
            await conn.commit()

    @staticmethod
    async def health_check() -> bool:
        """Check database connectivity."""
        try:
            engine = get_engine()
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
                return True
        except Exception:
            return False


from sqlalchemy import text
