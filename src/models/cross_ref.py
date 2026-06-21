# src/models/cross_ref.py
"""Cross Reference model for AP Automation Core Engine.

Tracks confirmed matches between invoices, POs, and delivery notes.
Used by the learning system to improve future matching accuracy.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin


class CrossRef(TimestampMixin, UUIDMixin, Base):
    """Cross Reference for tracking document matches.

    Records the relationship between matched documents (invoice, PO, DN)
    and maintains learning statistics for the matching engine.
    """

    __tablename__ = "cross_refs"

    # Document references
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        doc="Matched invoice ID",
    )
    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
        doc="Matched purchase order ID",
    )
    delivery_note_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
        doc="Matched delivery note ID",
    )

    # Match details
    match_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        doc="Type: exact, fuzzy, manual, learned",
    )
    match_score: Mapped[float] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        doc="Matching confidence score (0-1)",
    )
    match_decision: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        doc="Decision: auto_approve, one_click, exception, reject",
    )

    # Match confirmation
    confirmed: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        doc="Whether this match has been confirmed",
    )
    confirmed_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="User who confirmed this match",
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when match was confirmed",
    )

    # Rejection tracking
    rejected: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        doc="Whether this match was rejected",
    )
    rejected_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="User who rejected this match",
    )
    rejected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when match was rejected",
    )

    # Learning system tracking
    learning_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="learning",
        doc="Learning status: learning, promoted, demoted, rejected",
    )
    match_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        doc="Number of times this match pattern has been used",
    )
    success_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of successful matches using this pattern",
    )
    failure_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of failed matches using this pattern",
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Last time this pattern was used",
    )

    # Financial matching details (for audit)
    total_invoice_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Total invoice amount in match",
    )
    total_po_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Total PO amount in match",
    )
    variance_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        doc="Amount variance between invoice and PO",
    )
    variance_percentage: Mapped[float] = mapped_column(
        Numeric(8, 4),
        nullable=False,
        default=0.0,
        doc="Percentage variance between invoice and PO",
    )

    # Matched line counts
    matched_line_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of invoice lines matched",
    )
    total_line_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Total number of invoice lines",
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
        doc="Additional notes about this match",
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="cross_refs",
        foreign_keys=[invoice_id],
    )
    purchase_order: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder",
        back_populates="cross_refs",
        foreign_keys=[purchase_order_id],
    )
    delivery_note: Mapped["DeliveryNote | None"] = relationship(
        "DeliveryNote",
        back_populates="cross_refs",
        foreign_keys=[delivery_note_id],
    )

    __table_args__ = (
        Index("ix_cross_refs_invoice_id", "invoice_id"),
        Index("ix_cross_refs_purchase_order_id", "purchase_order_id"),
        Index("ix_cross_refs_delivery_note_id", "delivery_note_id"),
        Index("ix_cross_refs_match_decision", "match_decision"),
        Index("ix_cross_refs_confirmed", "confirmed"),
        Index("ix_cross_refs_learning_status", "learning_status"),
        Index("ix_cross_refs_match_type", "match_type"),
    )

    def __repr__(self) -> str:
        return f"<CrossRef Invoice:{self.invoice_id} PO:{self.purchase_order_id} Score:{self.match_score}>"

    @property
    def success_rate(self) -> float:
        """Calculate success rate of this match pattern."""
        if self.match_count == 0:
            return 0.0
        return self.success_count / self.match_count

    def record_success(self) -> None:
        """Record a successful use of this match pattern."""
        self.success_count += 1
        self.match_count += 1
        self.last_used_at = datetime.utcnow()

    def record_failure(self) -> None:
        """Record a failed use of this match pattern."""
        self.failure_count += 1
        self.match_count += 1
        self.last_used_at = datetime.utcnow()
