// src/app/services/user_service.py
"""User service."""

from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.services.base import BaseService


class UserService(BaseService[User]):
    """Service for user operations."""

    def __init__(self, db: Session):
        """Initialize user service."""
        super().__init__(User, db)

    def get_by_email(self, email: str) -> User | None:
        """Get a user by email."""
        return self.db.query(User).filter(User.email == email).first()

    def create(self, email: str, password: str, full_name: str) -> User:
        """Create a new user with hashed password."""
        hashed_password = hash_password(password)
        user_data = {
            "email": email,
            "hashed_password": hashed_password,
            "full_name": full_name,
        }
        return super().create(user_data)

    def authenticate(self, email: str, password: str) -> User | None:
        """Authenticate a user by email and password."""
        user = self.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def update_password(self, user: User, new_password: str) -> User:
        """Update user password."""
        hashed_password = hash_password(new_password)
        return self.update(user, {"hashed_password": hashed_password})

    def is_superuser(self, user_id: str) -> bool:
        """Check if user is a superuser."""
        user = self.get(user_id)
        return user.is_superuser if user else False
