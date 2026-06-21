// app/models/user.py
"""User model for authentication."""
import uuid
from typing import List, TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.matching import MatchConfirmation


class User(Base, UUIDMixin, TimestampMixin):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    confirmations: Mapped[List["MatchConfirmation"]] = relationship(
        "MatchConfirmation",
        back_populates="confirmed_by_user",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<User {self.email}>"
