# models/decision.py
# models/decision.py
"""Decision model for routing matching results."""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel

if TYPE_CHECKING:
    from models.match import Match
    from models.user import User


class DecisionType(str, Enum):
    """Decision type enumeration."""

    AUTO_APPROVE = "AUTO_APPROVE"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    DISPUTE = "DISPUTE"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    ESCALATE = "ESCALATE"


class Decision(BaseModel):
    """Decision model for routing matching results."""

    __tablename__ = "decisions"

    # Reference to match
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Decision details
    decision_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    decision_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
    )

    threshold_used: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
    )

    # Routing
    routed_to: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    routing_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Resolution
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    resolution_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Status
    is_pending: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    is_completed: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    # Human feedback (learning loop)
    human_confirmed: Mapped[bool | None] = mapped_column(
        nullable=True,
    )

    human_confirmed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )

    human_confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    human_feedback: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    match: Mapped["Match"] = relationship(
        "Match",
        foreign_keys=[match_id],
    )

    resolved_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[resolved_by],
    )

    human_confirmed_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[human_confirmed_by],
    )

    __table_args__ = (
        Index("ix_decision_match", "match_id"),
        Index("ix_decision_type_status", "decision_type", "is_pending"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Decision(match_id={self.match_id}, type={self.decision_type})>"
