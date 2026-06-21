# core/database.py
"""Async SQLAlchemy database session management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from core.config import settings


def create_async_engine_with_pool() -> AsyncEngine:
    """Create async engine with connection pooling."""
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DATABASE_ECHO,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_timeout=settings.DATABASE_POOL_TIMEOUT,
        pool_recycle=settings.DATABASE_POOL_RECYCLE,
        pool_pre_ping=True,
    )
    return engine


def create_async_engine_null_pool() -> AsyncEngine:
    """Create async engine without pooling (for testing)."""
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DATABASE_ECHO,
        poolclass=NullPool,
    )
    return engine


class DatabaseManager:
    """Manages async database engine and session factory."""

    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    def init(self, use_pool: bool = True) -> None:
        """Initialize the database engine and session factory."""
        if use_pool:
            self._engine = create_async_engine_with_pool()
        else:
            self._engine = create_async_engine_null_pool()

        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )

    async def close(self) -> None:
        """Close the database engine."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None

    @property
    def engine(self) -> AsyncEngine:
        """Get the async engine."""
        if self._engine is None:
            self.init()
        return self._engine  # type: ignore

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get the session factory."""
        if self._session_factory is None:
            self.init()
        return self._session_factory  # type: ignore

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session as a context manager."""
        session = self.session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """FastAPI dependency for getting a database session."""
        async with self.session() as session:
            yield session


# Global database manager instance
db_manager = DatabaseManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency to get database session.

    Yields:
        AsyncSession: Database session for the request.
    """
    async for session in db_manager.get_session():
        yield session


# Type alias for dependency injection
DbSession = Annotated[AsyncSession, Depends(get_db)]


class Base(DeclarativeBase):
    """SQLAlchemy declarative base class."""

    pass
