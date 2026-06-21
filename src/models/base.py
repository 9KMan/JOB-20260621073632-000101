// src/models/base.py
"""SQLAlchemy base configuration and database management."""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import create_engine, pool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, declared_attr

from config import get_cached_settings

logger = logging.getLogger(__name__)
settings = get_cached_settings()


class Base(DeclarativeBase):
    """SQLAlchemy declarative base with common configurations."""

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        return cls.__name__.lower()

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            result[column.name] = value
        return result


class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(self, engine):
        self.engine = engine
        self.session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    async def initialize(self) -> None:
        """Initialize database connection pool."""
        logger.info("Initializing database connection pool")
        # Test connection
        async with self.engine.begin() as conn:
            await conn.execute("SELECT 1")

    async def close(self) -> None:
        """Close database connection pool."""
        logger.info("Closing database connection pool")
        await self.engine.dispose()


# Create async engine
def get_database_url(async_mode: bool = True) -> str:
    """Get database URL with async driver if needed."""
    url = settings.DATABASE_URL
    
    if async_mode:
        if "postgresql://" in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://")
        elif "postgres://" in url:
            url = url.replace("postgres://", "postgresql+asyncpg://")
    
    return url


# Engine configuration
engine = create_async_engine(
    get_database_url(),
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    echo=settings.DEBUG,
)

# Session factory
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session context manager."""
    session: AsyncSession = async_session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI to get database session."""
    async for session in get_db_session():
        yield session
