# src/db/session.py
"""Database session utilities."""
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database import AsyncSessionLocal


async def get_db_session() -> AsyncSession:
    """Get a new database session."""
    async with AsyncSessionLocal() as session:
        yield session
