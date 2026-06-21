# models/cross_ref.py
"""Cross Reference model for AP Automation Core Engine - Learning Loop."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Float,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    ForeignKey,
    Boolean,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import MatchStatus, MatchConfidence

if TYPE_CHECKING:
    from models.invoice import InvoiceLineItem
    from models.purchase_order import PurchaseOrderLineItem


class CrossRef(Base, UUIDMixin, TimestampMixin):
    """
    Cross Reference model for the learning loop / matching history.
    
    This model stores confirmed matches between invoice line items and
    PO line items, enabling the system to learn and improve matching
    accuracy over time.
    
    Attributes:
        id: UUID primary key
        invoice_line_item_id: Reference to the invoice line item
        po_line_item_id: Reference to the PO line item
        balance_ledger_id: Reference to the balance ledger entry
        match_status: Current status of the match
        match_confidence: Confidence score (0-100)
        match_decision: How the match was made (auto, manual, etc.)
        price_match: Whether price matched
        quantity_match: Whether quantity matched
        supplier_match: Whether supplier matched
        date_match: Whether dates matched
        notes: Additional notes about the match
        confirmed_at: When the match was confirmed
        confirmed_by: Who confirmed the match
        is_auto_matched: Whether this was an automatic match
    """

    __tablename__ = "cross_refs"

    # References
    invoice_line_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_line_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    po_line_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_line_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    balance_ledger_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("balance_ledger.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Match status and confidence
    match_status: Mapped[MatchStatus] = mapped_column(
        default=MatchStatus.PENDING,
        nullable=False,
    )
    match_confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    confidence_level: Mapped[MatchConfidence] = mapped_column(
        default=MatchConfidence.LOW,
        nullable=False,
    )

    # Match decision
    match_decision: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    is_auto_matched: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Individual match criteria
    price_match: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    quantity_match: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supplier_match: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    date_match: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description_match: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Match scores
    price_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    quantity_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Variances
    price_variance: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0"),
        nullable=False,
    )
    quantity_variance: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0"),
        nullable=False,
    )
    price_variance_percent: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    quantity_variance_percent: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    # Confirmation tracking
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    confirmed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Match count for learning
    match_count: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    is_promoted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    invoice_line_item: Mapped["InvoiceLineItem"] = relationship(
        "InvoiceLineItem",
        back_populates="cross_refs",
        foreign_keys=[invoice_line_item_id],
    )
    po_line_item: Mapped["PurchaseOrderLineItem"] = relationship(
        "PurchaseOrderLineItem",
        foreign_keys=[po_line_item_id],
    )

    __table_args__ = (
        Index("ix_cross_refs_invoice_line_item_id", "invoice_line_item_id"),
        Index("ix_cross_refs_po_line_item_id", "po_line_item_id"),
        Index("ix_cross_refs_match_status", "match_status"),
        Index("ix_cross_refs_match_confidence", "match_confidence"),
        Index("ix_cross_refs_is_promoted", "is_promoted"),
    )

    def __repr__(self) -> str:
        return (
            f"<CrossRef InvoiceLine {self.invoice_line_item_id} -> "
            f"POLine {self.po_line_item_id} ({self.match_confidence:.1f}%)>"
        )

    def confirm(self, confirmed_by: str | None = None) -> None:
        """Mark this cross-reference as confirmed."""
        self.match_status = MatchStatus.CONFIRMED
        self.confirmed_at = datetime.utcnow()
        self.confirmed_by = confirmed_by
        self.match_count += 1

    def reject(self, notes: str | None = None) -> None:
        """Mark this cross-reference as rejected."""
        self.match_status = MatchStatus.REJECTED
        self.notes = notes

    def dismiss(self, notes: str | None = None) -> None:
        """Dismiss this cross-reference."""
        self.match_status = MatchStatus.DISMISSED
        self.notes = notes

    def promote(self) -> None:
        """Promote this match for future automatic matching."""
        self.is_promoted = True
