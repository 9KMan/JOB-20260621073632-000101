// src/models/user.py
"""User model for authentication."""
from sqlalchemy import Boolean, Column, String

from src.models.base import Base, BaseModel


class User(Base, BaseModel):
    """User model for authentication and authorization."""
    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    role = Column(String(50), default="user", nullable=False)

    def __repr__(self) -> str:
        return f"<User {self.username}>"
