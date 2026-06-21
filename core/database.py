# core/database.py
"""
Async SQLAlchemy database session management.

Provides async session factory, connection pool management,
and dependency injection helpers for FastAPI.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from core.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""

    pass


class DatabaseManager:
    """
    Manages database engine and session lifecycle.
    
    Provides async engine creation, session factory,
    and connection pool management.
    """

    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    @property
    def engine(self) -> AsyncEngine:
        """Get or create the async engine."""
        if self._engine is None:
            self._engine = self._create_engine()
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get or create the session factory."""
        if self._session_factory is None:
            self._session_factory = self._create_session_factory()
        return self._session_factory

    def _create_engine(self) -> AsyncEngine:
        """
        Create async SQLAlchemy engine with connection pooling.
        
        Uses PGBouncer endpoint for production, direct PostgreSQL for development.
        """
        engine_config = {
            "url": settings.database_pool_url,
            "echo": settings.debug,
            "pool_size": settings.database_pool_size,
            "max_overflow": settings.database_max_overflow,
            "pool_timeout": settings.database_pool_timeout,
            "pool_recycle": settings.database_pool_pool_recycle
            if hasattr(settings, "database_pool_recycle")
            else 3600,
            "pool_pre_ping": True,
            "connect_args": {
                "server_settings": {
                    "application_name": "ap_automation_engine",
                    "timezone": "UTC",
                },
                "timeout": 30,
            },
        }

        # Use NullPool for PGBouncer to avoid connection issues
        if "pgbouncer" in settings.database_pool_url.lower():
            engine_config["poolclass"] = NullPool

        logger.info(
            f"Creating database engine with pool_size={settings.database_pool_size}, "
            f"max_overflow={settings.database_max_overflow}"
        )

        return create_async_engine(**engine_config)

    def _create_session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Create async session factory."""
        return async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

    async def dispose(self) -> None:
        """Dispose of the engine and close all connections."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("Database engine disposed")

    async def ensure_connectivity(self) -> bool:
        """Verify database connectivity."""
        try:
            async with self.session_factory() as session:
                await session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database connectivity check failed: {e}")
            return False


# Global database manager instance
db_manager = DatabaseManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions.
    
    Yields an async session and ensures proper cleanup.
    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    session = db_manager.session_factory()
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
    """
    Context manager for database sessions outside of FastAPI routes.
    
    Usage:
        async with get_db_context() as db:
            result = await db.execute(select(Model))
    """
    session = db_manager.session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def init_db() -> None:
    """
    Initialize database - create all tables.
    
    Note: Use Alembic migrations for production database setup.
    This is mainly for testing and development.
    """
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")


async def close_db() -> None:
    """Close database connections on application shutdown."""
    await db_manager.dispose()
    logger.info("Database connections closed")
