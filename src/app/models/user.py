// src/app/models/user.py
"""
User model for authentication.
"""
from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship

from app.models.base import Base, UUIDPrimaryKey, TimestampMixin


class User(Base, UUIDPrimaryKey, TimestampMixin):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    role = Column(String(50), default="user", nullable=False)  # admin, user, reviewer

    # Relationships
    match_confirmations = relationship(
        "MatchResult",
        back_populates="confirmed_by_user",
        foreign_keys="MatchResult.confirmed_by_id",
    )

    def __repr__(self) -> str:
        return f"<User {self.username}>"
