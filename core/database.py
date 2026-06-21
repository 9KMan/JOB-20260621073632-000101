# core/database.py
"""Async SQLAlchemy database session management.

Provides async database sessions using SQLAlchemy 2.0 async support.
Connection pooling is configured via settings.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated, Any

from sqlalchemy import MetaData, create_engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from core.config import settings


# Naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


# Metadata with naming convention
metadata = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base class.

    All models inherit from this base class.
    Provides created_at and updated_at timestamp columns.
    """

    metadata = metadata

    type_annotation_map = {
        # Custom type annotations can be added here
    }


# Async Engine Configuration
async_engine = create_async_engine(
    settings.database.database_url,
    pool_size=settings.database.database_pool_size,
    max_overflow=settings.database.database_max_overflow,
    pool_timeout=settings.database.database_pool_timeout,
    echo=settings.database.database_echo,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Async Session Factory
AsyncSessionFactory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# Sync Engine (for migrations and Alembic)
engine = create_engine(
    settings.database_url,
    pool_size=settings.database.database_pool_size,
    max_overflow=settings.database.database_max_overflow,
    pool_timeout=settings.database.database_pool_timeout,
    echo=settings.database.database_echo,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Sync Session Factory (for migrations)
SyncSessionFactory = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class DatabaseSession:
    """Database session context manager.

    Usage:
        async with DatabaseSession() as session:
            result = await session.execute(query)
    """

    def __init__(self) -> None:
        self.session: AsyncSession | None = None

    async def __aenter__(self) -> AsyncSession:
        self.session = AsyncSessionFactory()
        return self.session

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.session is not None:
            if exc_type is not None:
                await self.session.rollback()
            await self.session.close()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI to get async database session.

    Usage:
        @app.get("/items")
        async def get_items(session: AsyncSession = Depends(get_async_session)):
            ...
    """
    async with DatabaseSession() as session:
        try:
            yield session
        finally:
            await session.close()


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Alternative async session getter for non-FastAPI contexts."""
    async with DatabaseSession() as session:
        yield session


async def init_db() -> None:
    """Initialize database tables.

    Creates all tables defined in the models.
    Should be called once during application startup.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections.

    Should be called during application shutdown.
    """
    await async_engine.dispose()


async def check_db_health() -> bool:
    """Check database connection health.

    Returns:
        bool: True if database is reachable, False otherwise.
    """
    try:
        async with DatabaseSession() as session:
            await session.execute("SELECT 1")
        return True
    except Exception:
        return False


__all__ = [
    "Base",
    "metadata",
    "convention",
    "engine",
    "async_engine",
    "AsyncSessionFactory",
    "SyncSessionFactory",
    "AsyncSession",
    "Session",
    "DatabaseSession",
    "get_async_session",
    "get_db",
    "init_db",
    "close_db",
    "check_db_health",
]
