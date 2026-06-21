// core/database.py
"""Async SQLAlchemy database session management.

This module provides async database connection and session management
for PostgreSQL using SQLAlchemy 2.0 async capabilities.

Connection pooling is handled by SQLAlchemy's async engine with configurable
pool settings to optimize performance for the AP automation workload.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any, Dict, Optional

from sqlalchemy import MetaData, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool

from core.config import get_settings

logger = logging.getLogger(__name__)

# Naming convention for database constraints
NAMING_CONVENTION: Dict[str, Any] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
    "source_table": "%(table_name)s",
    "referred_table": "%(referred_table_name)s",
    "column": "%(column_0_name)s",
}

# Global metadata object
metadata = MetaData(naming_convention=NAMING_CONVENTION)


class DatabaseManager:
    """Manages async database engine and session factory.
    
    Provides centralized database connection management with proper
    resource cleanup and configurable pooling for production workloads.
    """

    def __init__(self) -> None:
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None
        self._initialized: bool = False

    @property
    def engine(self) -> AsyncEngine:
        """Get the async engine instance."""
        if self._engine is None:
            raise RuntimeError("Database not initialized. Call init_db() first.")
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get the session factory."""
        if self._session_factory is None:
            raise RuntimeError("Database not initialized. Call init_db() first.")
        return self._session_factory

    async def init_db(self, database_url: Optional[str] = None) -> None:
        """Initialize the database engine and session factory.
        
        Creates an async engine with connection pooling configured
        based on application settings.
        
        Args:
            database_url: Optional database URL override.
        """
        if self._initialized:
            logger.warning("Database already initialized")
            return

        settings = get_settings()
        
        # Use provided URL or get from settings
        url = database_url or settings.database.database_url
        
        # Determine pool class based on environment
        pool_class = NullPool if settings.is_production else AsyncAdaptedQueuePool

        # Engine configuration
        engine_kwargs: Dict[str, Any] = {
            "url": url,
            "echo": settings.database.database_echo,
            "echo_pool": False,
            "pool_size": settings.database.database_pool_size,
            "max_overflow": settings.database.database_max_overflow,
            "pool_timeout": settings.database.database_pool_timeout,
            "poolclass": pool_class,
            "pool_pre_ping": True,  # Verify connections before use
            "pool_recycle": 3600,  # Recycle connections after 1 hour
        }

        # Create async engine
        self._engine = create_async_engine(**engine_kwargs)

        # Create session factory with scoped configuration
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,  # Don't expire objects after commit
            autoflush=False,  # Manual flush control
            autocommit=False,  # Explicit transaction management
        )

        self._initialized = True
        logger.info(
            "Database initialized",
            extra={
                "url": url.split("@")[-1] if "@" in url else "local",
                "pool_size": settings.database.database_pool_size,
            },
        )

    async def close_db(self) -> None:
        """Close the database engine and cleanup resources."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            self._initialized = False
            logger.info("Database connections closed")

    async def create_tables(self, base: Any) -> None:
        """Create all tables defined in the models.
        
        Uses metadata from the declarative base to create tables.
        Primarily used in testing or initial setup.
        
        Args:
            base: SQLAlchemy declarative base class.
        """
        async with self.engine.begin() as conn:
            await conn.run_sync(base.metadata.create_all)
        logger.info("Database tables created")

    async def drop_tables(self, base: Any) -> None:
        """Drop all tables defined in the models.
        
        WARNING: This will delete all data. Use only in testing
        or development environments.
        
        Args:
            base: SQLAlchemy declarative base class.
        """
        async with self.engine.begin() as conn:
            await conn.run_sync(base.metadata.drop_all)
        logger.warning("Database tables dropped")

    async def health_check(self) -> bool:
        """Check database connectivity.
        
        Returns:
            bool: True if database is reachable, False otherwise.
        """
        try:
            async with self.session_factory() as session:
                await session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global database manager instance
db_manager = DatabaseManager()


# Convenience functions for backward compatibility
async def init_db(database_url: Optional[str] = None) -> None:
    """Initialize the database."""
    await db_manager.init_db(database_url)


async def close_db() -> None:
    """Close the database."""
    await db_manager.close_db()


def get_engine() -> AsyncEngine:
    """Get the database engine."""
    return db_manager.engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get the session factory."""
    return db_manager.session_factory


# Import Base for table creation
from models.base import Base

# Create typed session local
AsyncSessionLocal = async_sessionmaker(
    bind=db_manager.engine if db_manager._engine else None,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for getting async database session.
    
    Yields an AsyncSession that is automatically closed after use.
    Handles transaction management and rollback on errors.
    
    Yields:
        AsyncSession: Database session for the request.
    """
    if not db_manager._initialized:
        await db_manager.init_db()

    async with db_manager.session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for getting async database session.
    
    Alternative to get_db() for use outside of FastAPI request context.
    Useful in background workers or scripts.
    
    Yields:
        AsyncSession: Database session.
    """
    if not db_manager._initialized:
        await db_manager.init_db()

    async with db_manager.session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Alias for get_db() for backward compatibility."""
    async for session in get_db():
        yield session


# SQLAlchemy Base class - re-exported here for convenience
Base = Base
