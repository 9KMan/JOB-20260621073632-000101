// src/models/user.py
"""User model for authentication."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel, SoftDeleteMixin
from src.models.enums import UserRole

if TYPE_CHECKING:
    from src.models.match import Match


class User(BaseModel, SoftDeleteMixin):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
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
    role: Mapped[UserRole] = mapped_column(
        UserRole.enum,
        default=UserRole.VIEWER,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    last_login: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    confirmed_matches: Mapped[list["Match"]] = relationship(
        "Match",
        back_populates="confirmed_by_user",
        foreign_keys="Match.confirmed_by_id",
    )
    rejected_matches: Mapped[list["Match"]] = relationship(
        "Match",
        back_populates="rejected_by_user",
        foreign_keys="Match.rejected_by_id",
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"
