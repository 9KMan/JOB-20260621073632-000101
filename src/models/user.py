# src/models/user.py
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.matching import MatchingResult


class User(BaseModel):
    """
    User model for authentication and authorization.
    """
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_email", "email", unique=True),
        Index("ix_users_username", "username", unique=True),
    )

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="user", nullable=False)

    # Relationships
    matching_results: Mapped[list["MatchingResult"]] = relationship(
        "MatchingResult",
        back_populates="reviewed_by_user",
        foreign_keys="MatchingResult.reviewed_by_id"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
