"""Async SQLAlchemy engine + session management.

We expose a single ``AsyncEngine`` per process and a FastAPI-friendly
``AsyncSession`` factory via ``get_session``. Sessions are scoped to a request
and are rolled back on exceptions by the dependency itself.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.config import get_settings

logger = logging.getLogger(__name__)


def _build_engine() -> AsyncEngine:
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_pre_ping=True,
        pool_recycle=1800,
        echo=settings.db_echo,
        future=True,
    )


# Module-level engine/session factory. A single engine per process is the
# recommended pattern; re-creating engines per request leaks connections.
_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def get_engine() -> AsyncEngine:
    """Return (and lazily build) the process-wide async engine."""
    global _engine
    if _engine is None:
        _engine = _build_engine()
        logger.info("Initialized async SQLAlchemy engine")
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the async session factory bound to the engine."""
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


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding an ``AsyncSession`` per request.

    Commits on clean exit; rolls back on exception and re-raises.
    """
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Context manager for ad-hoc scripts and background workers."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def dispose_engine() -> None:
    """Dispose of the engine at shutdown.

    Safe to call multiple times; required for graceful FastAPI shutdown so that
    pooled connections are returned cleanly.
    """
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        logger.info("Disposed async SQLAlchemy engine")
    _engine = None
    _session_factory = None


async def healthcheck() -> bool:
    """Lightweight DB ping used by the API health endpoint."""
    engine = get_engine()
    try:
        async with engine.connect() as conn:
            await conn.exec_driver_sql("SELECT 1")
        return True
    except SQLAlchemyError as exc:
        logger.warning("Database healthcheck failed: %s", exc)
        return False
