// models/audit.py
// models/audit.py
"""Audit log model for tracking all changes."""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel


class AuditLog(BaseModel):
    """Audit log for tracking all system changes."""
    
    __tablename__ = "audit_logs"
    
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # CREATE, UPDATE, DELETE, MATCH, APPROVE, REJECT, etc.
    
    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # invoice, purchase_order, delivery_note, match, etc.
    
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    
    old_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    
    new_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
    )
    
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="audit_logs",
    )
    
    def __repr__(self) -> str:
        return f"<AuditLog {self.action} {self.entity_type} {self.entity_id}>"
