// core/database.py
"""Async SQLAlchemy database session management.

Provides async database engine, session factory, and FastAPI dependencies.
Optimized for PostgreSQL with connection pooling.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from core.config import get_settings


# ============================================
# Async Engine Configuration
# ============================================

def create_async_engine_with_settings() -> AsyncEngine:
    """Create async engine with settings from environment."""
    settings = get_settings()
    
    return create_async_engine(
        settings.get_database_url(),
        pool_size=settings.database.pool_size,
        max_overflow=settings.database.max_overflow,
        pool_timeout=settings.database.pool_timeout,
        pool_recycle=settings.database.pool_recycle,
        pool_pre_ping=True,
        echo=settings.database.echo,
        echo_pool=settings.database.echo_pool,
    )


# Global async engine instance
engine: AsyncEngine = create_async_engine_with_settings()

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ============================================
# Sync Engine (for Alembic migrations)
# ============================================

def create_sync_engine() -> create_engine:
    """Create sync engine for Alembic migrations."""
    settings = get_settings()
    sync_url = settings.get_database_url().replace(
        "postgresql+asyncpg://", "postgresql://"
    )
    
    return create_engine(
        sync_url,
        pool_size=settings.database.pool_size,
        max_overflow=settings.database.max_overflow,
        pool_timeout=settings.database.pool_timeout,
        pool_recycle=settings.database.pool_recycle,
        pool_pre_ping=True,
        echo=settings.database.echo,
    )


# ============================================
# Database Session Dependency
# ============================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions.

    Yields:
        AsyncSession: SQLAlchemy async session.
    
    Example:
        