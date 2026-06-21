# src/db/init_db.py
"""Initialize database with default data."""
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.user import User
from src.app.services.auth import get_password_hash


async def init_db(db: AsyncSession) -> None:
    """Initialize database with default admin user if not exists."""
    from sqlalchemy import select
    
    # Check if admin user exists
    result = await db.execute(
        select(User).where(User.username == "admin")
    )
    existing_admin = result.scalar_one_or_none()
    
    if not existing_admin:
        admin_user = User(
            username="admin",
            email="admin@finaro.com",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            is_superuser=True,
            full_name="System Administrator",
        )
        db.add(admin_user)
        await db.commit()
