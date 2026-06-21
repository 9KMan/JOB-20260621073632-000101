# core/database.py
"""Async SQLAlchemy database session management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy import MetaData, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from core.config import Settings, get_settings


# Naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """SQLAlchemy declarative base class."""

    metadata = MetaData(naming_convention=convention)


# Async engine and session factory
_async_engine = None
_async_session_factory = None

# Sync engine and session factory (for migrations)
_sync_engine = None
_sync_session_factory = None


def get_async_engine(settings: Settings | None = None) -> Any:
    """Get or create async engine."""
    global _async_engine
    if _async_engine is None:
        if settings is None:
            settings = get_settings()
        _async_engine = create_async_engine(
            settings.database.database_url,
            pool_size=settings.database.database_pool_size,
            max_overflow=settings.database.database_max_overflow,
            pool_timeout=settings.database.database_pool_timeout,
            pool_recycle=settings.database.database_pool_recycle,
            echo=settings.database.database_echo,
            pool_pre_ping=True,
        )
    return _async_engine


def get_async_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create async session factory."""
    global _async_session_factory
    if _async_session_factory is None:
        engine = get_async_engine()
        _async_session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return _async_session_factory


def get_sync_engine(settings: Settings | None = None) -> Any:
    """Get or create sync engine for migrations."""
    global _sync_engine
    if _sync_engine is None:
        if settings is None:
            settings = get_settings()
        # Convert async URL to sync URL for migrations
        sync_url = settings.database.database_url.replace(
            "postgresql+asyncpg://", "postgresql://"
        )
        _sync_engine = create_engine(
            sync_url,
            pool_size=settings.database.database_pool_size,
            max_overflow=settings.database.database_max_overflow,
            echo=settings.database.database_echo,
            pool_pre_ping=True,
        )
    return _sync_engine


def get_sync_session_factory() -> sessionmaker[Session]:
    """Get or create sync session factory."""
    global _sync_session_factory
    if _sync_session_factory is None:
        engine = get_sync_engine()
        _sync_session_factory = sessionmaker(
            engine,
            class_=Session,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return _sync_session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides an async database session.
    
    Yields:
        AsyncSession: SQLAlchemy async session
    """
    session_factory = get_async_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions outside of FastAPI dependencies.
    
    Yields:
        AsyncSession: SQLAlchemy async session
    """
    session_factory = get_async_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Initialize database tables."""
    engine = get_async_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    global _async_engine, _sync_engine
    if _async_engine is not None:
        await _async_engine.dispose()
        _async_engine = None
    if _sync_engine is not None:
        _sync_engine.dispose()
        _sync_engine = None
