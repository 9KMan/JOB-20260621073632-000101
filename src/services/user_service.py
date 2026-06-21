// src/services/user_service.py
"""User service for authentication and authorization."""
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.config import config
from src.models.user import User
from src.schemas.user import UserCreate, UserUpdate, UserResponse, Token, TokenData
from src.services.base import BaseService


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService(BaseService[User]):
    """Service for user management and authentication."""

    def __init__(self, db: Session):
        """Initialize user service."""
        super().__init__(User, db)

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()

    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self.db.query(User).filter(User.username == username).first()

    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user with hashed password."""
        hashed_password = self.hash_password(user_data.password)
        user_dict = user_data.model_dump(exclude={"password"})
        user_dict["hashed_password"] = hashed_password
        return self.create(user_dict)

    def update_user(self, id: str, user_data: UserUpdate) -> Optional[User]:
        """Update user with optional password change."""
        update_dict = user_data.model_dump(exclude_unset=True)
        if "password" in update_dict and update_dict["password"]:
            update_dict["hashed_password"] = self.hash_password(update_dict.pop("password"))
        return self.update(id, update_dict)

    def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password."""
        user = self.get_by_username(username)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user

    def create_access_token(self, user: User) -> Token:
        """Create JWT access token for user."""
        expires_delta = timedelta(minutes=config.jwt.access_token_expire_minutes)
        expire = datetime.utcnow() + expires_delta
        to_encode = {
            "sub": user.id,
            "username": user.username,
            "role": user.role,
            "exp": expire,
        }
        encoded_jwt = jwt.encode(
            to_encode,
            config.jwt.secret_key,
            algorithm=config.jwt.algorithm,
        )
        return Token(
            access_token=encoded_jwt,
            token_type="bearer",
            expires_in=config.jwt.access_token_expire_minutes * 60,
        )

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def decode_token(token: str) -> Optional[TokenData]:
        """Decode and validate JWT token."""
        try:
            payload = jwt.decode(
                token,
                config.jwt.secret_key,
                algorithms=[config.jwt.algorithm],
            )
            user_id = payload.get("sub")
            username = payload.get("username")
            role = payload.get("role")
            if user_id is None:
                return None
            return TokenData(user_id=user_id, username=username, role=role)
        except JWTError:
            return None

    def get_active_users(self) -> list[User]:
        """Get all active users."""
        return self.db.query(User).filter(User.is_active == True).all()

    def deactivate_user(self, id: str) -> Optional[User]:
        """Deactivate a user."""
        return self.update(id, {"is_active": False})

    def activate_user(self, id: str) -> Optional[User]:
        """Activate a user."""
        return self.update(id, {"is_active": True})
