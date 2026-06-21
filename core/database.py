# core/database.py
"""Async SQLAlchemy database session management.

Provides:
- AsyncEngine and AsyncSession factory
- Session dependency for FastAPI
- Database health check utilities
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool

from core.config import settings


def create_async_engine_with_pool() -> AsyncEngine:
    """Create async engine with connection pooling."""
    pool_class = (
        NullPool if settings.debug else AsyncAdaptedQueuePool
    )

    return create_async_engine(
        str(settings.database_url),
        echo=settings.database_echo,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_timeout=settings.database_pool_timeout,
        poolclass=pool_class,
        pool_pre_ping=True,
        connect_args={
            "server_settings": {
                "application_name": "ap-automation-engine",
                "timezone": "UTC",
            },
        },
    )


# Global engine instance
engine: AsyncEngine = create_async_engine_with_pool()

# Session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions.

    Yields:
        AsyncSession: Database session that auto-closes on exit.

    Example:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db_session)):
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
async def get_db_session_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database sessions outside of FastAPI.

    Yields:
        AsyncSession: Database session with automatic commit/rollback.

    Example:
        async with get_db_session_context() as session:
            session.add(invoice)
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


async def get_db_session_dependency() -> AsyncSession:
    """Get a database session for use with FastAPI dependency injection.

    Note: This is an alternative to Depends(get_db_session) that can be
    used when you need to manage the session lifecycle manually.

    Returns:
        AsyncSession: Database session instance.
    """
    session = AsyncSessionLocal()
    try:
        return session
    except Exception:
        await session.close()
        raise


async def check_database_health() -> dict[str, bool | str]:
    """Check database connection health.

    Returns:
        dict: Health status with connection and version info.
    """
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT version()"))
            version = result.scalar()
            return {
                "healthy": True,
                "version": version,
                "status": "connected",
            }
    except Exception as e:
        return {
            "healthy": False,
            "status": "disconnected",
            "error": str(e),
        }


async def close_db_connections() -> None:
    """Close all database connections.

    Call this during application shutdown.
    """
    await engine.dispose()
