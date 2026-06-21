# src/models/audit_log.py
"""Audit Log model for tracking system changes."""
from sqlalchemy import Column, String, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.models.base import Base, UUIDMixin, TimestampMixin


class AuditLog(Base, UUIDMixin, TimestampMixin):
    """Audit Log model for tracking all system changes."""
    
    __tablename__ = "audit_logs"
    
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Action type: CREATE, UPDATE, DELETE, MATCH, APPROVE, REJECT, etc.
    action = Column(String(50), nullable=False, index=True)
    
    # Entity information
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Old and new values
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    
    # Additional context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    request_id = Column(String(100), nullable=True)
    
    # Description
    description = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action}, entity_type={self.entity_type})>"
