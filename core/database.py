# core/database.py
"""
Async SQLAlchemy 2.0 session management with connection pooling.

Provides async engine, session factory, and FastAPI dependency injection.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool, QueuePool

from core.config import settings

# Global async engine instance
_async_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def create_async_db_engine() -> AsyncEngine:
    """
    Create async SQLAlchemy engine with connection pooling.
    
    Returns:
        Configured AsyncEngine instance with pooling.
    """
    engine_kwargs: dict[str, object] = {
        "echo": settings.database.echo,
        "echo_pool": settings.debug,
        "pool_recycle": settings.database.pool_recycle,
        "pool_timeout": settings.database.pool_timeout,
    }

    # Use NullPool for testing, QueuePool otherwise
    if settings.is_testing:
        engine_kwargs["poolclass"] = NullPool
    else:
        engine_kwargs["poolclass"] = AsyncAdaptedQueuePool
        engine_kwargs["pool_size"] = settings.database.pool_size
        engine_kwargs["max_overflow"] = settings.database.max_overflow

    return create_async_engine(
        str(settings.database.url),
        **engine_kwargs,
    )


def get_async_engine() -> AsyncEngine:
    """Get or create the global async engine instance."""
    global _async_engine
    if _async_engine is None:
        _async_engine = create_async_db_engine()
    return _async_engine


def get_async_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create the global async session factory."""
    global _async_session_factory
    if _async_session_factory is None:
        engine = get_async_engine()
        _async_session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return _async_session_factory


# Expose engine and factory
async_engine = get_async_engine()
async_session_factory = get_async_session_factory()


class AsyncSessionLocal:
    """
    Async session context manager factory.
    
    Usage:
        async with AsyncSessionLocal() as session:
            result = await session.execute(query)
    """

    def __init__(self) -> None:
        self._factory = async_session_factory

    async def __aenter__(self) -> AsyncSession:
        self.session = self._factory()
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            await self.session.rollback()
        await self.session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for async database sessions.
    
    Yields an AsyncSession and handles commit/rollback automatically.
    Commits on success, rolls back on exception.
    
    Usage:
        @app.post("/invoices")
        async def create_invoice(session: AsyncSession = Depends(get_db)):
            ...
    """
    factory = get_async_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Alternative context manager pattern for get_db.
    
    Usage:
        async with get_db_context() as session:
            result = await session.execute(query)
    """
    factory = get_async_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for manual session management.
    
    Usage:
        async with get_db_session() as session:
            result = await session.execute(query)
    """
    factory = get_async_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """
    Initialize database — create all tables.
    
    Called on application startup.
    For production, use Alembic migrations instead.
    """
    from models.base import Base
    engine = get_async_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Close database connections gracefully.
    
    Called on application shutdown.
    """
    global _async_engine, _async_session_factory
    if _async_engine is not None:
        await _async_engine.dispose()
        _async_engine = None
    _async_session_factory = None


async def check_db_health() -> dict[str, object]:
    """
    Check database connectivity and return health status.
    
    Returns:
        Dict with status, latency_ms, and connection info.
    """
    import time
    factory = get_async_session_factory()
    async with factory() as session:
        start = time.perf_counter()
        await session.execute(text("SELECT 1"))
        latency_ms = (time.perf_counter() - start) * 1000
        await session.commit()
        return {
            "status": "healthy",
            "latency_ms": round(latency_ms, 2),
            "pool_size": settings.database.pool_size,
            "max_overflow": settings.database.max_overflow,
        }


async def run_migrations() -> None:
    """Run Alembic migrations programmatically."""
    from alembic.config import Config
    from alembic.runtime.environment import EnvironmentContext
    from alembic.runtime.migration import MigrationContext
    from alembic import command

    engine = get_async_engine()
    alembic_cfg = Config("alembic.ini")

    async with engine.begin() as conn:
        await conn.run_sync(_run_alembic_upgrade, alembic_cfg)


def _run_alembic_upgrade(connection, alembic_cfg) -> None:
    """Synchronous helper to run Alembic upgrade."""
    from alembic import command
    command.upgrade(alembic_cfg, "head")
