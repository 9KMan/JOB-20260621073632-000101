# src/services/user.py
"""User service."""
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.models.user import User
from src.schemas.user import UserCreate, UserUpdate
from src.services.auth import AuthService


class UserService:
    """Service for user management."""

    def __init__(self, db: Session):
        """Initialize user service with database session."""
        self.db = db

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination."""
        return self.db.query(User).offset(skip).limit(limit).all()

    def get_total_count(self) -> int:
        """Get total count of users."""
        return self.db.query(User).count()

    def create(self, user_data: UserCreate) -> User:
        """Create new user."""
        user = User(
            email=user_data.email,
            hashed_password=AuthService.hash_password(user_data.password),
            full_name=user_data.full_name,
            role=user_data.role,
            is_active=True,
            is_superuser=False,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user_id: UUID, user_data: UserUpdate) -> Optional[User]:
        """Update existing user."""
        user = self.get_by_id(user_id)
        if not user:
            return None

        update_data = user_data.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["hashed_password"] = AuthService.hash_password(
                update_data.pop("password")
            )

        for field, value in update_data.items():
            setattr(user, field, value)

        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user_id: UUID) -> bool:
        """Delete user."""
        user = self.get_by_id(user_id)
        if not user:
            return False

        self.db.delete(user)
        self.db.commit()
        return True

    def deactivate(self, user_id: UUID) -> Optional[User]:
        """Deactivate user."""
        user = self.get_by_id(user_id)
        if not user:
            return None

        user.is_active = False
        self.db.commit()
        self.db.refresh(user)
        return user

    def activate(self, user_id: UUID) -> Optional[User]:
        """Activate user."""
        user = self.get_by_id(user_id)
        if not user:
            return None

        user.is_active = True
        self.db.commit()
        self.db.refresh(user)
        return user
