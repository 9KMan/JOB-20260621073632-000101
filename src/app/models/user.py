// src/app/models/user.py
"""User model for authentication."""
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.models.base import BaseModel


class User(BaseModel):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="user", nullable=False)
    
    match_records: Mapped[list["MatchRecord"]] = relationship(  # noqa: F821
        "MatchRecord",
        back_populates="reviewed_by_user",
        foreign_keys="MatchRecord.reviewed_by",
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"
