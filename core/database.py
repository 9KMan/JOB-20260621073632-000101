// core/database.py
"""Async SQLAlchemy database session management.

This module provides async database session management with:
- Connection pooling
- Async session factory
- Context managers for session handling
- Automatic transaction management
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from core.config import settings

# Create async engine with connection pooling
engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_timeout=settings.database_pool_timeout,
    pool_recycle=settings.database_pool_recycle,
    pool_pre_ping=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI to get database session.

    Yields:
        AsyncSession: Database session that auto-closes after use

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
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database sessions.

    Useful for non-FastAPI contexts like background workers.

    Yields:
        AsyncSession: Database session

    Example:
        async with get_db_context() as db:
            result = await db.execute(select(Item))
            items = result.scalars().all()
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
    """Initialize database connection and verify connectivity.

    This function tests the database connection and logs
    the connection status.
    """
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print("Database connection established successfully")
    except Exception as e:
        print(f"Database connection failed: {e}")
        raise


async def close_db() -> None:
    """Close database connections and dispose the engine.

    Should be called during application shutdown.
    """
    await engine.dispose()
    print("Database connections closed")


async def health_check() -> bool:
    """Check database health and connectivity.

    Returns:
        bool: True if database is healthy, False otherwise
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def create_tables_if_not_exist() -> None:
    """Create all tables if they don't exist.

    Note: This is mainly for development/testing.
    Use Alembic migrations for production.
    """
    from models.base import Base

    # Import models to ensure they are registered with Base
    from models import invoice, purchase_order, delivery_note, balance_ledger, cross_ref  # noqa: F401

    import asyncio
    from sqlalchemy import create_engine

    # Create sync engine for table creation
    sync_url = settings.database_url_sync
    sync_engine = create_engine(sync_url, echo=False)

    Base.metadata.create_all(bind=sync_engine)
    sync_engine.dispose()
