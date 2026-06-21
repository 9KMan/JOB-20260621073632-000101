# src/services/auth.py
"""Authentication service."""
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.config import get_settings
from src.models.user import User
from src.schemas.user import UserCreate
from src.schemas.common import Token, TokenData

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication service for user management and JWT tokens."""

    def __init__(self, db: Session):
        """Initialize auth service with database session."""
        self.db = db

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user by email and password."""
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user

    def create_access_token(
        self,
        user_id: str,
        email: str,
        role: str,
        expires_delta: Optional[timedelta] = None,
    ) -> Token:
        """Create JWT access token."""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.access_token_expire_minutes
            )

        to_encode = {
            "sub": str(user_id),
            "email": email,
            "role": role,
            "exp": expire,
            "type": "access",
        }

        encoded_jwt = jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.algorithm,
        )

        return Token(
            access_token=encoded_jwt,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
        )

    def create_refresh_token(
        self,
        user_id: str,
        email: str,
        role: str,
    ) -> Token:
        """Create JWT refresh token."""
        expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)

        to_encode = {
            "sub": str(user_id),
            "email": email,
            "role": role,
            "exp": expire,
            "type": "refresh",
        }

        encoded_jwt = jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.algorithm,
        )

        return Token(
            access_token=encoded_jwt,
            token_type="bearer",
            expires_in=settings.refresh_token_expire_days * 24 * 60 * 60,
        )

    @staticmethod
    def decode_token(token: str) -> Optional[TokenData]:
        """Decode and validate JWT token."""
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.algorithm],
            )
            user_id: str = payload.get("sub")
            email: str = payload.get("email")
            role: str = payload.get("role")
            token_type: str = payload.get("type")

            if user_id is None:
                return None

            return TokenData(
                user_id=user_id,
                email=email,
                role=role,
            )
        except JWTError:
            return None

    def get_current_user(self, token: str) -> Optional[User]:
        """Get current user from JWT token."""
        token_data = self.decode_token(token)
        if token_data is None:
            return None

        user = self.db.query(User).filter(User.id == token_data.user_id).first()
        return user
