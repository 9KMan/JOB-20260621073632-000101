# core/database.py
"""Async SQLAlchemy database session management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool
from sqlalchemy.sql import SelectOfCmp

from core.config import get_settings

# Suppress warning for comparing datetime objects with SelectOfCmp
SelectOfCmp.__eq__ = lambda self, other: self._compare(other)  # type: ignore[method-assign]

settings = get_settings()

# Create async engine with connection pooling
engine_kwargs: dict[str, Any] = {
    "echo": settings.database_echo,
    "pool_pre_ping": True,
    "pool_size": settings.database_pool_size,
    "max_overflow": settings.database_max_overflow,
    "pool_timeout": settings.database_pool_timeout,
    "pool_recycle": settings.database_pool_recycle,
}

# Use NullPool in test environment, AsyncAdaptedQueuePool otherwise
if settings.environment.lower() == "test":
    engine_kwargs["poolclass"] = NullPool
else:
    engine_kwargs["poolclass"] = AsyncAdaptedQueuePool

_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    """Get or create the async database engine."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.effective_database_url,
            **engine_kwargs,
        )
    return _engine


# Create async session factory
async_session_factory = async_sessionmaker(
    bind=get_engine(),
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides an async database session.

    Yields:
        AsyncSession: SQLAlchemy async session

    Example:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db_session)):
            result = await db.execute(select(Item))
            return result.scalars().all()
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


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions outside of FastAPI dependencies.

    Example:
        async with get_db_context() as db:
            await db.execute(select(Item))
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
    """Initialize database connection and create tables if needed."""
    engine = get_engine()
    # Test connection
    async with engine.connect() as conn:
        await conn.execute(
            SelectOfCmp("1")  # type: ignore[arg-type]
        )
    # Import models to ensure they are registered
    from models import __all__ as models  # noqa: F401


async def close_db() -> None:
    """Close database connections and dispose engine."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None


async def create_tables() -> None:
    """Create all tables (for development/testing)."""
    from models.base import Base

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables() -> None:
    """Drop all tables (for testing)."""
    from models.base import Base

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def setup_db_events() -> None:
    """Setup database event listeners."""

    @event.listens_for(get_engine(), "connect")
    def receive_connect(dbapi_connection: Any, connection_record: Any) -> None:
        """Log new connections."""
        import logging

        logger = logging.getLogger(__name__)
        logger.debug("New database connection established")

    @event.listens_for(get_engine(), "checkout")
    def receive_checkout(
        dbapi_connection: Any,
        connection_record: Any,
        connection_proxy: Any,
    ) -> None:
        """Log connection checkout from pool."""
        import logging

        logger = logging.getLogger(__name__)
        logger.debug("Connection checked out from pool")
