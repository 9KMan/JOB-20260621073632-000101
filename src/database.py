// src/database.py
"""Database connection and session management."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.config import get_settings

settings = get_settings()

# Synchronous engine (for migrations and CLI)
sync_engine = create_engine(
    settings.database.url,
    echo=settings.database.echo,
    **settings.database.pool_config,
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

# Async engine (for FastAPI)
async_database_url = settings.database.url.replace(
    "postgresql://", "postgresql+asyncpg://"
)

async_engine = create_async_engine(
    async_database_url,
    echo=settings.database.echo,
    **settings.database.pool_config,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


def get_db() -> Session:
    """Get synchronous database session (for migrations)."""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session (for FastAPI dependency injection)."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
