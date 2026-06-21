// models/cross_ref.py
"""Cross-Reference model for the learning loop functionality."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, CustomMixin
from models.enums import DecisionType, LearningStatus, MatchConfidence

if TYPE_CHECKING:
    from models.delivery_note import DeliveryNote
    from models.invoice import Invoice
    from models.purchase_order import PurchaseOrder


class CrossRef(Base, CustomMixin):
    """Cross-Reference table for learning loop and confirmed matches.

    This table stores:
    - Confirmed matches between Invoice/PO/DN
    - Learning data for improving future matches
    - Match history and confidence scores

    Attributes:
        invoice_id: Reference to invoice.
        purchase_order_id: Reference to purchase order.
        delivery_note_id: Reference to delivery note (optional).
        match_score: Calculated match score (0-100).
        confidence: Match confidence level.
        decision: Match decision type.
        match_type: Type of match (exact, fuzzy, manual).
        price_variance: Price difference if any.
        quantity_variance: Quantity difference if any.
        variance_percentage: Total variance percentage.
        status: Learning status.
        confirmed_by: User who confirmed the match.
        confirmed_at: Timestamp of confirmation.
        usage_count: Number of times this match pattern was used.
        last_used_at: Timestamp of last usage.
    """

    __tablename__ = "cross_refs"
    __table_args__ = (
        Index("ix_cross_ref_invoice_id", "invoice_id"),
        Index("ix_cross_ref_po_id", "purchase_order_id"),
        Index("ix_cross_ref_dn_id", "delivery_note_id"),
        Index("ix_cross_ref_match_score", "match_score"),
        Index("ix_cross_ref_confidence", "confidence"),
        Index("ix_cross_ref_status", "status"),
        Index("ix_cross_ref_created_at", "created_at"),
        {"schema": None},
    )

    # Document references
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    delivery_note_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Match scoring
    match_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    confidence: Mapped[str] = mapped_column(
        String(20),
        default=MatchConfidence.NONE.value,
        nullable=False,
    )
    decision: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    # Match type
    match_type: Mapped[str] = mapped_column(
        String(20),
        default="fuzzy",
        nullable=False,
    )

    # Variance analysis
    price_variance: Mapped[Decimal] = mapped_column(
        Decimal(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    quantity_variance: Mapped[Decimal] = mapped_column(
        Decimal(12, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    variance_percentage: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    # Learning loop
    status: Mapped[str] = mapped_column(
        String(20),
        default=LearningStatus.ACTIVE.value,
        nullable=False,
    )
    confirmed_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    usage_count: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Pattern matching data
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    po_number_pattern: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    invoice_number_pattern: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Additional data
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="cross_refs",
        foreign_keys=[invoice_id],
    )
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="cross_refs",
        foreign_keys=[purchase_order_id],
    )
    delivery_note: Mapped["DeliveryNote | None"] = relationship(
        "DeliveryNote",
        back_populates="cross_refs",
        foreign_keys=[delivery_note_id],
    )

    def __repr__(self) -> str:
        return f"<CrossRef {self.invoice_id} -> {self.purchase_order_id} ({self.match_score})>"

    def promote(self) -> None:
        """Promote this cross-ref pattern to higher confidence."""
        if self.status == LearningStatus.ACTIVE.value:
            self.status = LearningStatus.PROMOTED.value
            self.usage_count += 1
            self.last_used_at = datetime.now()

    def demote(self) -> None:
        """Demote this cross-ref pattern."""
        if self.status == LearningStatus.PROMOTED.value:
            self.status = LearningStatus.DEMOTED.value
