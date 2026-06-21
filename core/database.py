# core/database.py
"""Async SQLAlchemy database session management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from core.config import settings


# Async engine for FastAPI
engine: AsyncEngine = create_async_engine(
    settings.app.database.url,
    echo=settings.app.database.echo,
    pool_size=settings.app.database.pool_size,
    max_overflow=settings.app.database.max_overflow,
    pool_timeout=settings.app.database.pool_timeout,
    pool_recycle=settings.app.database.pool_recycle,
    pool_pre_ping=True,
)

# Async session factory
async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI to get an async database session.
    
    Yields:
        AsyncSession: SQLAlchemy async session
    
    Example:
        @app.get("/items")
        async def get_items(session: AsyncSession = Depends(get_db_session)):
            result = await session.execute(select(Item))
            return result.scalars().all()
    """
    async with async_session_factory() as session:
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
    Context manager for database session outside of FastAPI dependencies.
    
    Yields:
        AsyncSession: SQLAlchemy async session
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    from models.base import Base
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()


class DatabaseHelper:
    """Helper class for database operations."""

    def __init__(self) -> None:
        self.engine = engine
        self.session_factory = async_session_factory

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a new database session."""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def execute_query(self, query, session: AsyncSession | None = None) -> list:
        """Execute a query and return results."""
        if session:
            result = await session.execute(query)
            return list(result.scalars().all())
        
        async with self.session() as s:
            result = await s.execute(query)
            return list(result.scalars().all())


# Global database helper instance
db_helper = DatabaseHelper()
