// src/models/user.py
"""User model for authentication."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.matching import MatchDecision


class User(Base):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Relationships
    match_decisions: Mapped[list["MatchDecision"]] = relationship(
        "MatchDecision", back_populates="reviewed_by_user"
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"
