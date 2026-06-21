// core/database.py
"""Async SQLAlchemy database session management.

This module provides async database session management using SQLAlchemy 2.0
async capabilities with PostgreSQL asyncpg driver.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from core.config import settings


# Create async engine with connection pooling
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_pre_ping=True,
    connect_args={
        "server_settings": {
            "jit": "off",
            "timezone": "UTC",
        }
    },
)

# Create async session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class DatabaseManager:
    """Database manager for async operations."""

    @staticmethod
    async def create_tables() -> None:
        """Create all database tables."""
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @staticmethod
    async def drop_tables() -> None:
        """Drop all database tables (use with caution)."""
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    @staticmethod
    async def health_check() -> bool:
        """Check database connectivity.

        Returns:
            True if database is healthy, False otherwise.
        """
        try:
            async with async_session_factory() as session:
                await session.execute(text("SELECT 1"))
                return True
        except Exception:
            return False

    @staticmethod
    async def close() -> None:
        """Close all database connections."""
        await engine.dispose()


# SQLAlchemy declarative base
class Base(DeclarativeBase):
    """SQLAlchemy declarative base class."""

    type_annotation_map = {
        str: TEXT,
    }


# Type alias for TEXT column
from sqlalchemy import String

TEXT = String().with_variant(String(65535), "mysql")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI to get async database session.

    Yields:
        AsyncSession: SQLAlchemy async session.

    Example:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
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
    """Context manager for database session (for non-FastAPI use).

    Yields:
        AsyncSession: SQLAlchemy async session.
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


# Common column types for models
class TimestampMixin:
    """Mixin for created_at and updated_at timestamp columns."""

    created_at: Mapped[datetime] = mapped_column(
        default=None,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=None,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )


from datetime import datetime
