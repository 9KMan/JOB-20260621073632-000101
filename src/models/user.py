// src/models/user.py
"""User model for authentication."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.models.base import BaseModel


class User(BaseModel):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(default=False, nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="user", nullable=False)

    # Relationships
    match_confirmations: Mapped[list["MatchConfirmation"]] = relationship(
        back_populates="confirmed_by_user",
        foreign_keys="MatchConfirmation.confirmed_by",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"
