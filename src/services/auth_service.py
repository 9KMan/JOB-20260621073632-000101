// src/services/auth_service.py
"""Authentication service with JWT token handling."""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.models.user import User
from src.schemas.auth import Token, TokenData, UserCreate, UserResponse, UserMeResponse

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Service for handling authentication and user management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Generate password hash."""
        return pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + (
            expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
        )
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

    def decode_token(self, token: str) -> Optional[TokenData]:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            return TokenData(
                sub=payload.get("sub"),
                exp=datetime.fromtimestamp(payload.get("exp", 0)),
                permissions=payload.get("permissions", []),
            )
        except JWTError:
            return None

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email address."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get a user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        user = User(
            email=user_data.email,
            hashed_password=self.get_password_hash(user_data.password),
            full_name=user_data.full_name,
            role=user_data.role,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate a user with email and password."""
        user = await self.get_user_by_email(email)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user

    async def create_token_for_user(self, user: User) -> Token:
        """Create an access token for a user."""
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "permissions": ["read", "write"] if user.is_active else [],
        }
        access_token = self.create_access_token(token_data)
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
        )

    def user_to_response(self, user: User) -> UserResponse:
        """Convert User model to response schema."""
        return UserResponse.model_validate(user)

    def user_to_me_response(self, user: User) -> UserMeResponse:
        """Convert User model to me response schema."""
        return UserMeResponse.model_validate(user)
