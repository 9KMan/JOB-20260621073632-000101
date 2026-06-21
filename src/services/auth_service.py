// src/services/auth_service.py
"""Authentication service for user management and JWT tokens."""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from jose import jwt
from pydantic import EmailStr
from sqlalchemy.orm import Session

from src.app.config import get_settings
from src.models.user import User, UserRole

settings = get_settings()


class AuthService:
    """Service for authentication and user management."""

    def __init__(self, db: Session):
        """Initialize auth service."""
        self.db = db

    def create_user(
        self,
        email: str,
        username: str,
        password: str,
        full_name: Optional[str] = None,
        role: UserRole = UserRole.VIEWER,
    ) -> User:
        """Create a new user."""
        user = User(
            email=email,
            username=username,
            hashed_password=User.hash_password(password),
            full_name=full_name,
            role=role.value,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == UUID(user_id)).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self.db.query(User).filter(User.username == username).first()

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password."""
        user = self.get_user_by_username(username)
        if not user:
            return None
        if not user.verify_password(password):
            return None
        return user

    def create_access_token(self, user: User) -> str:
        """Create JWT access token for user."""
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.utcnow() + expires_delta
        to_encode = {
            "sub": str(user.id),
            "email": user.email,
            "username": user.username,
            "role": user.role,
            "exp": expire,
        }
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    def create_refresh_token(self, user: User) -> str:
        """Create JWT refresh token for user."""
        expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        expire = datetime.utcnow() + expires_delta
        to_encode = {
            "sub": str(user.id),
            "type": "refresh",
            "exp": expire,
        }
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[dict]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            return payload
        except jwt.JWTError:
            return None

    def update_last_login(self, user: User) -> None:
        """Update user's last login timestamp."""
        user.last_login = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)

    def change_password(self, user: User, old_password: str, new_password: str) -> bool:
        """Change user password."""
        if not user.verify_password(old_password):
            return False
        user.hashed_password = User.hash_password(new_password)
        self.db.commit()
        return True

    def reset_password(self, user: User, new_password: str) -> None:
        """Reset user password (admin function)."""
        user.hashed_password = User.hash_password(new_password)
        self.db.commit()

    def deactivate_user(self, user: User) -> None:
        """Deactivate user account."""
        user.is_active = False
        self.db.commit()

    def activate_user(self, user: User) -> None:
        """Activate user account."""
        user.is_active = True
        self.db.commit()
