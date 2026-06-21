// src/services/auth_service.py
"""Authentication service."""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.app.config import get_settings
from src.models.user import User
from src.models.enums import UserRole
from src.schemas.user import UserCreate, UserLogin, TokenResponse

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Service for authentication operations."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes)
        )
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    @staticmethod
    def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(days=settings.jwt_refresh_token_expire_days)
        )
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    @staticmethod
    def decode_token(token: str) -> dict:
        """Decode and verify a JWT token."""
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])

    @staticmethod
    def create_tokens(user: User) -> TokenResponse:
        """Create access and refresh tokens for a user."""
        token_data = {"sub": str(user.id), "email": user.email, "role": user.role.value}
        return TokenResponse(
            access_token=AuthService.create_access_token(token_data),
            refresh_token=AuthService.create_refresh_token(token_data),
        )

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate a user by email and password."""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        if not AuthService.verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user

    @staticmethod
    def get_user_by_id(db: Session, user_id: uuid.UUID) -> Optional[User]:
        """Get a user by ID."""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get a user by email."""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """Create a new user."""
        hashed_password = AuthService.hash_password(user_data.password)
        user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            role=user_data.role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_user(db: Session, user: User, user_data: dict) -> User:
        """Update a user's information."""
        for key, value in user_data.items():
            if value is not None:
                if key == "password":
                    setattr(user, "hashed_password", AuthService.hash_password(value))
                else:
                    setattr(user, key, value)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def create_default_admin(db: Session) -> Optional[User]:
        """Create a default admin user if none exists."""
        admin_email = "admin@finaro.com"
        existing = AuthService.get_user_by_email(db, admin_email)
        if existing:
            return existing
        
        admin = User(
            email=admin_email,
            hashed_password=AuthService.hash_password("admin123!"),
            full_name="System Administrator",
            role=UserRole.ADMIN,
            is_active=True,
            is_superuser=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin
