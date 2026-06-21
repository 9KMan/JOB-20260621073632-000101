# src/core/database.py
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.core.config import settings


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


# Async engine for FastAPI
async_engine = create_async_engine(
    settings.database_url_async,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    **settings.get_database_config()
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# Sync engine for migrations and scripts
sync_engine = create_engine(
    settings.DATABASE_URL_SYNC,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

# Sync session factory
SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides an async database session.
    Automatically handles transaction commits and cleanup.
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


def get_sync_db() -> Session:
    """
    Get synchronous database session for migrations and scripts.
    """
    return SyncSessionLocal()


async def init_db() -> None:
    """
    Initialize database tables.
    Called on application startup.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Close database connections.
    Called on application shutdown.
    """
    await async_engine.dispose()
