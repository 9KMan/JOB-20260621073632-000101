# src/models/audit.py
from sqlalchemy import Column, String, Text, ForeignKey, JSON
from src.models.base import BaseModel


class AuditLog(BaseModel):
    """Audit Log model for tracking all changes."""

    __tablename__ = "audit_logs"

    entity_type = Column(String(50), nullable=False, index=True)  # invoice, po, dn, matching_result
    entity_id = Column(String(36), nullable=False, index=True)
    action = Column(String(50), nullable=False, index=True)  # create, update, delete, match, approve, reject
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    changes = Column(JSON, nullable=True)  # Store before/after values
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
