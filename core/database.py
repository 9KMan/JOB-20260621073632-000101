# core/database.py
"""Async SQLAlchemy session management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, QueuePool

from core.config import settings

# ── Engine ────────────────────────────────────────────────────────────────────

_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    """Lazily create / return the global async engine."""
    global _engine
    if _engine is None:
        pool_class: type[QueuePool] = QueuePool
        pool_kwargs = {
            "pool_size": settings.database_pool_size,
            "max_overflow": settings.database_max_overflow,
            "pool_timeout": settings.database_pool_timeout,
            "pool_pre_ping": True,
        }

        # Use NullPool when DATABASE_URL points to PGBouncer (transaction mode)
        # so SQLAlchemy doesn't try to manage physical connections directly.
        if "pgbouncer" in settings.database_url.lower() or "6432" in settings.database_url:
            pool_class = NullPool  # type: ignore[assignment]
            pool_kwargs = {"pool_pre_ping": True}

        _engine = create_async_engine(
            settings.database_url,
            echo=settings.database_echo,
            poolclass=pool_class,
            **pool_kwargs,
        )
    return _engine


# ── Session factory ────────────────────────────────────────────────────────────

_AsyncSessionLocal: async_sessionmaker[AsyncSession] | None = None


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Lazily create / return the global async session factory."""
    global _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        _AsyncSessionLocal = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return _AsyncSessionLocal


AsyncSessionLocal = get_session_factory()


# ── Session injection ─────────────────────────────────────────────────────────

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency — yields an AsyncSession and ensures it is closed.

    Usage in route handlers::

        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    session: AsyncSession = AsyncSessionLocal()
    try:
        yield session
    finally:
        await session.close()


# ── Context manager helper ────────────────────────────────────────────────────

@asynccontextmanager
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Standalone async context manager for use outside FastAPI DI."""
    session: AsyncSession = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


# ── Lifecycle ─────────────────────────────────────────────────────────────────

async def dispose_engine() -> None:
    """Call on application shutdown to release all pool connections."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
