# core/database.py
"""Async SQLAlchemy database session management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool

from core.config import settings


def _get_effective_database_url() -> str:
    """Get the effective database URL, respecting PGBouncer override."""
    if settings.database.pgbouncer_host:
        # Reconstruct URL with PGBouncer host/port
        base_url = settings.database.database_url
        # Extract parts from the URL
        if "://" in base_url:
            protocol, rest = base_url.split("://", 1)
            if "@" in rest:
                credentials_host, db_name = rest.rsplit("@", 1)
                host_port, _ = credentials_host.split("/", 1) if "/" in credentials_host else (credentials_host, "")
                if "/" in host_port:
                    credentials, host = host_port.split("@", 1)
                else:
                    credentials = ""
                    host = host_port
                return f"{protocol}://{credentials}@{settings.database.pgbouncer_host}:{settings.database.pgbouncer_port}/{db_name.split('/')[-1]}"
    return settings.database.database_url


engine = create_async_engine(
    _get_effective_database_url(),
    echo=settings.database.echo_sql,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=settings.database.pool_size,
    max_overflow=settings.database.max_overflow,
    pool_timeout=settings.database.pool_timeout,
    pool_pre_ping=True,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI to get async database session."""
    async with async_session_maker() as session:
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
    """Context manager for database session (for non-FastAPI use)."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


DbSession = Annotated[AsyncSession, Depends(get_db)]
