// src/models/user.py
"""User model for authentication."""
from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship

from src.models.base import BaseModel


class User(BaseModel):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

    # Relationships
    match_decisions = relationship(
        "MatchDecision", back_populates="reviewed_by_user", lazy="dynamic"
    )
