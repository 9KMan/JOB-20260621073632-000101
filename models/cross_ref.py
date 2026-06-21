# models/cross_ref.py
"""CrossRef SQLAlchemy model.

Learning loop table that stores confirmed matches for pattern recognition.
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Boolean,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from models.invoice import Invoice, InvoiceLine
    from models.purchase_order import PurchaseOrder, PurchaseOrderLine
    from models.delivery_note import DeliveryNote, DeliveryNoteLine


class CrossRef(Base, UUIDMixin, TimestampMixin):
    """Cross-reference model for learned match patterns.

    Stores confirmed matches between invoices, POs, and delivery notes
    to enable the learning loop for future automatic matching.

    Attributes:
        confidence_score: How confident the system is in this match
        match_count: Number of times this pattern has been confirmed
        is_promoted: Whether this pattern has been promoted to auto-match
        vendor_id: Vendor for this pattern
        sku: Product SKU (if applicable)
    """

    __tablename__ = "cross_refs"

    # Match type classification
    match_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    confidence_level: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # Frequency and learning
    match_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    confirmation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rejection_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_promoted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    promoted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Vendor/Product pattern
    vendor_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    vendor_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    description_pattern: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Price tolerance learned
    price_tolerance_percent: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    quantity_tolerance_percent: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Learned values
    learned_unit_price: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    learned_unit_of_measure: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Score thresholds at time of learning
    match_score: Mapped[float] = mapped_column(Float, nullable=False)
    decision: Mapped[str] = mapped_column(String(50), nullable=False)

    # Invoice reference
    invoice_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    invoice_number: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    invoice_line_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="CASCADE"),
        nullable=True,
    )

    # PO reference
    purchase_order_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    po_number: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    po_line_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Delivery note reference
    delivery_note_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    dn_number: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    dn_line_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Additional context
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    confirmed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    invoice: Mapped["Invoice | None"] = relationship(
        "Invoice",
        back_populates="cross_refs",
    )
    purchase_order: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder",
        back_populates="cross_refs",
    )
    delivery_note: Mapped["DeliveryNote | None"] = relationship(
        "DeliveryNote",
        back_populates="cross_refs",
    )

    __table_args__ = (
        Index("ix_cross_ref_vendor_sku", "vendor_id", "sku"),
        Index("ix_cross_ref_match_type", "match_type", "is_promoted"),
        Index("ix_cross_ref_confidence", "confidence_level", "match_count"),
    )

    @property
    def is_trusted(self) -> bool:
        """Check if this pattern is trusted (high confirmation rate)."""
        total = self.confirmation_count + self.rejection_count
        if total == 0:
            return False
        return self.confirmation_count / total >= 0.8

    @property
    def promotion_threshold(self) -> int:
        """Minimum match count for promotion consideration."""
        return 5

    def should_promote(self) -> bool:
        """Check if this pattern should be promoted to auto-match."""
        if self.is_promoted:
            return False
        return (
            self.match_count >= self.promotion_threshold
            and self.is_trusted
        )

    def record_confirmation(self, confirmed_by: str | None = None) -> None:
        """Record a successful confirmation of this match pattern."""
        self.confirmation_count += 1
        self.match_count += 1
        self.confirmed_at = datetime.utcnow()
        self.confirmed_by = confirmed_by

    def record_rejection(self) -> None:
        """Record a rejection of this match pattern."""
        self.rejection_count += 1

    def promote(self) -> None:
        """Promote this pattern to auto-match status."""
        self.is_promoted = True
        self.promoted_at = datetime.utcnow()

    def __repr__(self) -> str:
        return f"<CrossRef {self.match_type} - {self.vendor_id}/{self.sku} ({self.match_count} matches)>"
