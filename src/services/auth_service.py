// src/services/auth_service.py
"""Authentication service."""
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.config import get_settings
from src.models.user import User
from src.models.enums import UserRole
from src.schemas.user import UserCreate, UserLogin
from src.services.base_service import BaseService

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService(BaseService[User, UserCreate, dict]):
    """Service for authentication operations."""
    
    def __init__(self, db: Session):
        super().__init__(User, db)
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user with hashed password.
        
        Args:
            user_data: User creation data
            
        Returns:
            Created user
        """
        db_user = User(
            email=user_data.email,
            hashed_password=self.hash_password(user_data.password),
            full_name=user_data.full_name,
            role=user_data.role,
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def authenticate(self, login_data: UserLogin) -> Optional[User]:
        """
        Authenticate a user by email and password.
        
        Args:
            login_data: Login credentials
            
        Returns:
            User if authenticated, None otherwise
        """
        user = self.get_by(email=login_data.email)
        if not user:
            return None
        if not self.verify_password(login_data.password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user
    
    def create_access_token(
        self,
        user: User,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token for a user.
        
        Args:
            user: The user to create token for
            expires_delta: Token expiration time
            
        Returns:
            JWT token string
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.access_token_expire_minutes
            )
        
        to_encode = {
            "sub": str(user.id),
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "role": user.role.value,
            "email": user.email,
        }
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )
        return encoded_jwt
    
    @staticmethod
    def decode_token(token: str) -> Optional[dict]:
        """
        Decode and validate a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Token payload or None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm]
            )
            return payload
        except JWTError:
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email address."""
        return self.get_by(email=email)
    
    def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get a user by ID."""
        return self.get(user_id)
