// src/models/user.py
"""User model for authentication and authorization."""
import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin, UUIDMixin
from src.models.enums import UserRole

if TYPE_CHECKING:
    from src.models.matching import MatchConfirmation


class User(Base, UUIDMixin, TimestampMixin):
    """User model for authentication."""
    
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    role: Mapped[UserRole] = mapped_column(
        String(50),
        default=UserRole.VIEWER,
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

    # Relationships
    match_confirmations: Mapped[List["MatchConfirmation"]] = relationship(
        "MatchConfirmation",
        back_populates="confirmed_by_user",
        foreign_keys="MatchConfirmation.confirmed_by",
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"
