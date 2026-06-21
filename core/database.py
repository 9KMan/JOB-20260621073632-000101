# core/database.py
"""Async SQLAlchemy database session management.

Provides async session factory and dependency injection for FastAPI.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool

from core.config import settings


if settings.DATABASE_URL.startswith("postgresql"):
    engine = create_async_engine(
        settings.DATABASE_URL,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_timeout=settings.DATABASE_POOL_TIMEOUT,
        pool_recycle=settings.DATABASE_POOL_RECYCLE,
        echo=settings.DATABASE_ECHO,
        pool_pre_ping=True,
    )
else:
    engine = create_async_engine(
        settings.DATABASE_URL,
        poolclass=NullPool,
        echo=settings.DATABASE_ECHO,
    )

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides an async database session.

    Yields:
        AsyncSession: An async SQLAlchemy session.

    Usage:
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
    """Context manager for database sessions outside of FastAPI dependencies.

    Yields:
        AsyncSession: An async SQLAlchemy session.

    Usage:
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
    """Initialize the database by creating all tables.

    This should be called during application startup.
    For production, use Alembic migrations instead.
    """
    from models.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections.

    This should be called during application shutdown.
    """
    await engine.dispose()
