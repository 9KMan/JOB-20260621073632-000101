# models/cross_ref.py
"""CrossRef SQLAlchemy model.

Learning loop / cross-reference table that stores confirmed matches
for improving future matching accuracy.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, UUIDMixin, TimestampMixin, TableNameMixin
from models.enums import LearningStatus, MatchSource, MatchConfidence


class CrossRef(Base, UUIDMixin, TimestampMixin, TableNameMixin):
    """Cross-reference table for learning loop.

    Stores confirmed matches between:
    - Invoice lines and PO lines
    - Invoice lines and DN lines
    - SKU patterns
    - Supplier patterns

    Used to improve matching accuracy over time through promotion
    and demotion of rules based on user confirmation.
    """

    __tablename__ = "cross_ref"
    __table_args__ = (
        UniqueConstraint(
            "invoice_line_id",
            "po_line_id",
            name="uq_cross_ref_invoice_po_line",
        ),
        UniqueConstraint(
            "invoice_line_id",
            "dn_line_id",
            name="uq_cross_ref_invoice_dn_line",
        ),
        Index("ix_cross_ref_invoice_line_id", "invoice_line_id"),
        Index("ix_cross_ref_po_line_id", "po_line_id"),
        Index("ix_cross_ref_dn_line_id", "dn_line_id"),
        Index("ix_cross_ref_supplier_id", "supplier_id"),
        Index("ix_cross_ref_sku", "sku"),
        Index("ix_cross_ref_learning_status", "learning_status"),
        Index("ix_cross_ref_match_count", "match_count"),
    )

    # Primary references
    invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="CASCADE"),
        nullable=True,
    )
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=True,
    )
    dn_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Pattern-based references
    supplier_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    supplier_sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    description_pattern: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Match metrics
    match_score: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )
    confidence: Mapped[MatchConfidence] = mapped_column(
        String(20),
        nullable=False,
    )
    source: Mapped[MatchSource] = mapped_column(
        String(20),
        nullable=False,
    )

    # Learning status
    learning_status: Mapped[LearningStatus] = mapped_column(
        String(20),
        nullable=False,
        default=LearningStatus.ACTIVE,
    )

    # Usage tracking
    match_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    success_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    failure_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_success_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Approval tracking
    is_approved: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    approved_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<CrossRef score={self.match_score} status={self.learning_status}>"

    @property
    def success_rate(self) -> float:
        """Calculate success rate of this cross-reference."""
        if self.match_count == 0:
            return 0.0
        return (self.success_count / self.match_count) * 100

    def record_match(self, success: bool) -> None:
        """Record a match attempt.

        Args:
            success: Whether the match was successful
        """
        self.match_count += 1
        self.last_used_at = datetime.utcnow()

        if success:
            self.success_count += 1
            self.last_success_at = datetime.utcnow()
        else:
            self.failure_count += 1
