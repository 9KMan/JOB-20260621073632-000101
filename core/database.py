# core/database.py
"""Async SQLAlchemy database session management.

Provides async session factory and dependency injection helpers.
Connection pooling is handled by SQLAlchemy's async engine.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any, Callable

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EngineManager:
    """Manages async SQLAlchemy engine lifecycle.
    
    Provides singleton engine instance with proper cleanup.
    """
    
    _engine: AsyncEngine | None = None
    _session_factory: async_sessionmaker[AsyncSession] | None = None
    
    @classmethod
    def get_engine(cls) -> AsyncEngine:
        """Get or create async engine instance."""
        if cls._engine is None:
            cls._engine = create_async_engine(
                settings.database_url,
                echo=settings.database_echo,
                pool_size=settings.database_pool_size,
                max_overflow=settings.database_max_overflow,
                pool_pre_ping=True,
                pool_recycle=3600,
                connect_args={
                    "server_settings": {
                        "application_name": "ap_automation",
                        "timezone": "UTC",
                    }
                },
            )
            logger.info(
                "Database engine created: %s",
                settings.database_url.split("@")[1] if "@" in settings.database_url else "localhost"
            )
        return cls._engine
    
    @classmethod
    def get_session_factory(cls) -> async_sessionmaker[AsyncSession]:
        """Get or create session factory."""
        if cls._session_factory is None:
            cls._session_factory = async_sessionmaker(
                bind=cls.get_engine(),
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False,
            )
        return cls._session_factory
    
    @classmethod
    async def close(cls) -> None:
        """Close engine and cleanup connections."""
        if cls._engine is not None:
            await cls._engine.dispose()
            cls._engine = None
            cls._session_factory = None
            logger.info("Database engine closed")


# Convenience accessors
def get_engine() -> AsyncEngine:
    """Get database engine instance."""
    return EngineManager.get_engine()


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get session factory instance."""
    return EngineManager.get_session_factory()


# Async session factory for dependency injection
AsyncSessionLocal = get_session_factory()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions.
    
    Yields:
        AsyncSession: SQLAlchemy async session
        
    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    session = AsyncSessionLocal()
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
    """Context manager for database sessions.
    
    Use this when not in FastAPI request context.
    
    Usage:
        async with get_db_context() as db:
            result = await db.execute(query)
    """
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def init_db() -> None:
    """Initialize database engine and create tables.
    
    Should be called on application startup.
    """
    engine = get_engine()
    logger.info("Database initialized")
    
    # Import models to register them with Base
    from models import base  # noqa: F401


async def close_db() -> None:
    """Close database connections.
    
    Should be called on application shutdown.
    """
    await EngineManager.close()
    logger.info("Database connections closed")


async def run_with_session(
    func: Callable[..., Any],
    *args: Any,
    **kwargs: Any
) -> Any:
    """Run a function within a database session context.
    
    Useful for background tasks or scripts.
    
    Args:
        func: Async function to run
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func
        
    Returns:
        Result of func call
    """
    async with get_db_context() as session:
        return await func(*args, session=session, **kwargs)
