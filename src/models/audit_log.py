// src/models/audit_log.py
"""Audit log model for compliance tracking."""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import BaseModel


class AuditAction(str, Enum):
    """Audit action types."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    MATCH = "match"
    CONFIRM = "confirm"
    REJECT = "reject"
    APPROVE = "approve"
    DISPUTE = "dispute"


class AuditLog(BaseModel):
    """Audit log for compliance and tracking."""

    __tablename__ = "audit_logs"

    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    user_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    old_values: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_values: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    metadata: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        Index("ix_audit_logs_entity", "entity_type", "entity_id"),
        Index("ix_audit_logs_timestamp_action", "timestamp", "action"),
    )
