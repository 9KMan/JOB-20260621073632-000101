// src/models/audit_log.py
"""Audit Log model for tracking system changes."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.user import User


class AuditAction(str):
    """Audit action types."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    MATCH = "match"
    APPROVE = "approve"
    REJECT = "reject"
    DISPUTE = "dispute"
    LOGIN = "login"
    LOGOUT = "logout"


class AuditLog(BaseModel):
    """Audit Log model for tracking all system changes."""

    __tablename__ = "audit_logs"

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    entity_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    changes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="audit_logs",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_al_user_id", "user_id"),
        Index("ix_al_entity", "entity_type", "entity_id"),
        Index("ix_al_timestamp", "timestamp"),
        Index("ix_al_action", "action"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog action={self.action} entity={self.entity_type} id={self.entity_id}>"


import uuid
