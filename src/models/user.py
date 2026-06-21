// src/models/user.py
"""User model for authentication."""
from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship

from src.models.base import BaseModel


class User(BaseModel):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    email: str = Column(String(255), unique=True, nullable=False, index=True)
    username: str = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password: str = Column(String(255), nullable=False)
    full_name: str = Column(String(255), nullable=True)
    is_active: bool = Column(Boolean, default=True, nullable=False)
    is_superuser: bool = Column(Boolean, default=False, nullable=False)
    role: str = Column(String(50), default="user", nullable=False)

    # Relationships
    matching_confirmations = relationship(
        "MatchingRecord",
        back_populates="confirmed_by_user",
        foreign_keys="MatchingRecord.confirmed_by_id",
    )

    def __repr__(self) -> str:
        return f"<User {self.username}>"
