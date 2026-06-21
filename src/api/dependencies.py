// src/api/dependencies.py
"""API dependencies."""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
