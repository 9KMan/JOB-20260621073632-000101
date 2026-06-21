// src/database.py
"""Database configuration and session management."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import NullPool
from typing import Generator

from src.config import get_settings


settings = get_settings()

# Create engine with connection pooling
if settings.debug:
    # Use NullPool for development to avoid connection issues
    engine = create_engine(
        settings.database_url,
        poolclass=NullPool,
        echo=settings.debug,
    )
else:
    # Use built-in pool for production
    engine = create_engine(
        settings.database_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_pre_ping=True,
        echo=False,
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


def get_db() -> Generator:
    """
    Dependency that provides a database session.
    
    Yields:
        Session: SQLAlchemy session instance
        
    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
