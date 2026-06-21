// src/models/user.py
"""User model for authentication."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.matching import MatchRecord, MatchDecision


class User(BaseModel):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    
    full_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    
    # Relationships
    decided_matches: Mapped[list["MatchRecord"]] = relationship(
        "MatchRecord",
        back_populates="decider",
        foreign_keys="MatchRecord.decided_by"
    )
    
    decision_history: Mapped[list["MatchDecision"]] = relationship(
        "MatchDecision",
        back_populates="user"
    )
    
    def __repr__(self) -> str:
        return f"<User {self.email}>"
