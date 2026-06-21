// src/app/models/user.py
"""
User Model
Authentication and authorization for the system.
"""
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class User(BaseModel):
    """User model for authentication."""
    
    __tablename__ = "users"
    
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(50),
        default="user",
        nullable=False,
    )
    
    def __repr__(self) -> str:
        return f"<User {self.username}>"
