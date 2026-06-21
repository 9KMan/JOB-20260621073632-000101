// core/database.py
"""Async SQLAlchemy session management."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import AsyncAdaptedQueuePool

from core.config import get_settings

logger = logging.getLogger(__name__)

# ── Engine ─────────────────────────────────────────────────────────────────────

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Lazily create (or return cached) async engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.db_echo,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_timeout=settings.db_pool_timeout,
            poolclass=AsyncAdaptedQueuePool,
            pool_pre_ping=True,
        )
        logger.info("Async engine created: pool_size=%d, max_overflow=%d",
                    settings.db_pool_size, settings.db_max_overflow)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Lazily create (or return cached) session factory."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return _session_factory


# Convenience aliases for backward compat
engine = get_engine()
AsyncSessionLocal = get_session_factory()


# ── Base ──────────────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    """SQLAlchemy declarative base — all models inherit from this."""
    pass


# ── Session Dependency ─────────────────────────────────────────────────────────

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an async session and ensures it is closed.
    Use with: async def endpoint(session: AsyncSession = Depends(get_db_session))
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context-manager version of get_db_session for use outside FastAPI routes."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def dispose_engine() -> None:
    """Dispose the engine — call on application shutdown."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("Async engine disposed")
