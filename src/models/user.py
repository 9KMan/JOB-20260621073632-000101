// src/models/user.py
"""User model for authentication."""
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel


class User(BaseModel, Base):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    email: Mapped[str] = mapped_column(
        String(length=255),
        unique=True,
        nullable=False,
        index=True,
    )
    username: Mapped[str] = mapped_column(
        String(length=100),
        unique=True,
        nullable=False,
        index=True,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(length=255),
        nullable=False,
    )
    full_name: Mapped[str | None] = mapped_column(
        String(length=255),
        nullable=True,
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
    
    def __repr__(self) -> str:
        return f"<User {self.email}>"
