// src/models/audit_log.py
"""Audit Log model for tracking all changes."""
from sqlalchemy import Column, Integer, String, Text

from src.models.base import Base, BaseModel


class AuditLog(Base, BaseModel):
    """Audit Log for tracking all system changes."""
    __tablename__ = "audit_logs"

    # Action details
    action = Column(String(50), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(String(36), nullable=True, index=True)
    
    # User info
    user_id = Column(String(36), nullable=True, index=True)
    username = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    # Change details
    old_values = Column(Text, nullable=True)  # JSON string
    new_values = Column(Text, nullable=True)  # JSON string
    changes = Column(Text, nullable=True)  # JSON string of changed fields
    
    # Additional context
    description = Column(Text, nullable=True)
    request_id = Column(String(36), nullable=True)
    
    # Severity
    severity = Column(String(20), default="INFO", nullable=False)  # DEBUG, INFO, WARNING, ERROR, CRITICAL

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} - {self.entity_type}>"
