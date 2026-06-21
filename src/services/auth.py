# src/services/auth.py
"""Authentication service."""
from typing import Optional
from datetime import datetime, timedelta

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.config import settings
from src.app.models.user import User
from src.schemas.user import UserCreate


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


async def get_user_by_username(
    db: AsyncSession,
    username: str
) -> Optional[User]:
    """Get a user by username."""
    result = await db.execute(
        select(User).where(
            User.username == username,
            User.is_deleted == "N"
        )
    )
    return result.scalar_one_or_none()


async def get_user_by_email(
    db: AsyncSession,
    email: str
) -> Optional[User]:
    """Get a user by email."""
    result = await db.execute(
        select(User).where(
            User.email == email,
            User.is_deleted == "N"
        )
    )
    return result.scalar_one_or_none()


async def get_user_by_id(
    db: AsyncSession,
    user_id: str
) -> Optional[User]:
    """Get a user by ID."""
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.is_deleted == "N"
        )
    )
    return result.scalar_one_or_none()


async def authenticate_user(
    db: AsyncSession,
    username: str,
    password: str
) -> Optional[User]:
    """Authenticate a user."""
    user = await get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user


async def create_user(
    db: AsyncSession,
    user_data: UserCreate
) -> User:
    """Create a new user."""
    # Check if username exists
    existing_user = await get_user_by_username(db, user_data.username)
    if existing_user:
        raise ValueError(f"Username '{user_data.username}' already exists")
    
    # Check if email exists
    existing_email = await get_user_by_email(db, user_data.email)
    if existing_email:
        raise ValueError(f"Email '{user_data.email}' already exists")
    
    # Create user
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        is_superuser=user_data.is_superuser,
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user
