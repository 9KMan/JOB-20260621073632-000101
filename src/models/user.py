// src/models/user.py
"""User model for authentication and authorization."""
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING

from src.models.base import BaseModel
from src.models.enums import UserRole, user_role_enum

if TYPE_CHECKING:
    from src.models.matching import Match


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
    
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    
    role: Mapped[UserRole] = mapped_column(
        user_role_enum,
        default=UserRole.VIEWER,
        nullable=False
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    
    # Relationships
    confirmed_matches: Mapped[List["Match"]] = relationship(
        "Match",
        back_populates="confirmed_by_user",
        foreign_keys="Match.confirmed_by_id",
        lazy="dynamic"
    )
    
    rejected_matches: Mapped[List["Match"]] = relationship(
        "Match",
        back_populates="rejected_by_user",
        foreign_keys="Match.rejected_by_id",
        lazy="dynamic"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
