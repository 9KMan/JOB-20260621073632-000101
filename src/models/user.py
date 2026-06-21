# src/models/user.py
"""User model."""
from sqlalchemy import Boolean, Column, String
from sqlalchemy.orm import relationship

from src.models.base import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin


class User(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    audit_logs = relationship("AuditLog", back_populates="user")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"
