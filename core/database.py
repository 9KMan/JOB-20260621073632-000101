// core/database.py
"""
Async SQLAlchemy database session management.

Provides:
- Async engine configuration with connection pooling
- Session factory for dependency injection
- Database initialization and teardown utilities
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool, NullPool

from core.config import settings


def _get_async_pool_args() -> dict:
    """Calculate async pool arguments based on settings."""
    return {
        "pool_size": settings.pool_size,
        "max_overflow": settings.max_overflow,
        "pool_timeout": settings.pool_timeout,
        "pool_recycle": settings.pool_recycle,
        "pool_pre_ping": True,
        "echo": settings.echo_sql,
    }


# Create async engine for the application
async_engine: AsyncEngine = create_async_engine(
    settings.database_url,
    **_get_async_pool_args(),
)

# Async session factory
AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# Sync engine for Alembic migrations (created lazily)
_sync_engine = None
_SyncSessionLocal = None


def get_sync_engine():
    """Get or create synchronous engine for migrations."""
    global _sync_engine, _SyncSessionLocal
    if _sync_engine is None:
        _sync_engine = create_engine(
            settings.database_url_sync,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            echo=settings.echo_sql,
        )
        _SyncSessionLocal = sessionmaker(
            bind=_sync_engine,
            autocommit=False,
            autoflush=False,
        )
    return _sync_engine


def get_sync_session_factory():
    """Get synchronous session factory."""
    get_sync_engine()  # Ensure engine is created
    return _SyncSessionLocal


async def init_db() -> None:
    """
    Initialize database connection and verify connectivity.
    
    This should be called during application startup.
    """
    try:
        # Test the connection
        async with async_engine.connect() as conn:
            await conn.execute(
                __import__("sqlalchemy").text("SELECT 1")
            )
    except Exception as e:
        raise RuntimeError(f"Failed to initialize database: {e}")


async def dispose_engine() -> None:
    """
    Properly dispose of the async engine.
    
    This should be called during application shutdown.
    """
    await async_engine.dispose()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides an async database session.
    
    Yields:
        AsyncSession: SQLAlchemy async session
        
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


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions outside of FastAPI.
    
    Use this for background tasks, scripts, or tests.
    
    Yields:
        AsyncSession: SQLAlchemy async session
        
    Example:
        async with get_db_context() as db:
            result = await db.execute(select(Invoice))
            invoices = result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_raw_connection():
    """
    Get a raw async connection for advanced use cases.
    
    Yields:
        Connection: SQLAlchemy async connection
        
    Note:
        Caller is responsible for closing the connection.
    """
    async with async_engine.connect() as conn:
        yield conn
