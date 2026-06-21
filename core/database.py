# core/database.py
"""Async SQLAlchemy database session management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker

from core.config import settings


class DataBaseManager:
    """Database manager for async SQLAlchemy operations.

    Provides async engine, session factory, and context managers
    for database operations.
    """

    def __init__(self) -> None:
        """Initialize the database manager with configuration from settings."""
        self._async_engine: AsyncEngine | None = None
        self._async_session_factory: async_sessionmaker[AsyncSession] | None = None
        self._sync_engine: Any = None
        self._sync_session_factory: sessionmaker[Session] | None = None

    @property
    def async_engine(self) -> AsyncEngine:
        """Get or create the async database engine."""
        if self._async_engine is None:
            self._async_engine = create_async_engine(
                settings.database_url,
                echo=settings.database_echo,
                pool_size=settings.database_pool_size,
                max_overflow=settings.database_max_overflow,
                pool_timeout=settings.database_pool_timeout,
                pool_recycle=settings.database_pool_recycle,
                pool_pre_ping=True,
            )
        return self._async_engine

    @property
    def async_session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get or create the async session factory."""
        if self._async_session_factory is None:
            self._async_session_factory = async_sessionmaker(
                bind=self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False,
            )
        return self._async_session_factory

    @property
    def sync_engine(self) -> Any:
        """Get or create the sync database engine (for migrations)."""
        if self._sync_engine is None:
            sync_url = settings.database_url.replace(
                "postgresql+asyncpg", "postgresql+psycopg2"
            )
            self._sync_engine = create_engine(
                sync_url,
                echo=settings.database_echo,
                pool_size=settings.database_pool_size,
                max_overflow=settings.database_max_overflow,
                pool_timeout=settings.database_pool_timeout,
                pool_recycle=settings.database_pool_recycle,
                pool_pre_ping=True,
            )
        return self._sync_engine

    @property
    def sync_session_factory(self) -> sessionmaker[Session]:
        """Get or create the sync session factory."""
        if self._sync_session_factory is None:
            self._sync_session_factory = sessionmaker(
                bind=self.sync_engine,
                autocommit=False,
                autoflush=False,
            )
        return self._sync_session_factory

    async def close(self) -> None:
        """Close all database connections and engines."""
        if self._async_engine is not None:
            await self._async_engine.dispose()
            self._async_engine = None
            self._async_session_factory = None

        if self._sync_engine is not None:
            self._sync_engine.dispose()
            self._sync_engine = None
            self._sync_session_factory = None

    async def ensure_tables(self) -> None:
        """Ensure all tables exist in the database."""
        from models.base import Base

        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)


# Global database manager instance
db_manager = DataBaseManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides an async database session.

    Yields:
        An async SQLAlchemy session that is automatically closed after use.
    """
    async with db_manager.async_session_factory() as session:
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
    """Context manager that provides an async database session.

    Yields:
        An async SQLAlchemy session that is automatically closed after use.
    """
    async with db_manager.async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_session() -> AsyncSession:
    """Get a new async database session without auto-commit.

    Returns:
        An async SQLAlchemy session. Caller is responsible for commit/rollback/close.
    """
    return db_manager.async_session_factory()
