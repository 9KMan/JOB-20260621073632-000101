// models/user.py
"""User model for authentication."""
import uuid
from sqlalchemy import Column, String, Boolean, Enum
from sqlalchemy.orm import relationship
import enum

from models.base import BaseModel


class UserRole(enum.Enum):
    """User roles for access control."""
    ADMIN = "admin"
    ACCOUNTANT = "accountant"
    VIEWER = "viewer"


class User(BaseModel):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.VIEWER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    matched_records = relationship("MatchingRecord", back_populates="matched_by_user")
    confirmed_records = relationship("MatchingRecord", foreign_keys="MatchingRecord.confirmed_by_id", back_populates="confirmed_by_user")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
