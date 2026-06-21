# models/cross_ref.py
"""CrossRef (Learning Loop) SQLAlchemy model."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from models.invoice import InvoiceLine
    from models.purchase_order import PurchaseOrderLine


class CrossRef(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Learning Loop / Cross-Reference table for match learning.
    
    Stores confirmed matches (invoice line <-> PO line) to build
    a reference database for future matching. Includes metadata
    about the match quality and user feedback.
    """

    __tablename__ = "cross_ref"
    __table_args__ = (
        Index("ix_cross_ref_po_line_id", "po_line_id"),
        Index("ix_cross_ref_invoice_line_id", "invoice_line_id"),
        Index("ix_cross_ref_sku", "sku"),
        Index("ix_cross_ref_vendor_number", "vendor_number"),
        Index("ix_cross_ref_match_confidence", "match_confidence"),
        Index("ix_cross_ref_promoted", "is_promoted"),
        UniqueConstraint(
            "po_line_id", "invoice_line_id",
            name="uq_cross_ref_po_invoice"
        ),
        UniqueConstraint(
            "vendor_number", "sku", "po_line_id",
            name="uq_cross_ref_vendor_sku_po"
        ),
    )

    # Line references
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Reference info
    invoice_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Invoice number at time of match",
    )
    po_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="PO number",
    )
    vendor_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Vendor number",
    )

    # Product matching info
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="SKU at time of match",
    )
    sku_normalized: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Normalized SKU for matching",
    )
    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Description at time of match",
    )

    # Match metrics
    match_confidence: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Match confidence score 0-100",
    )
    price_variance_pct: Mapped[Decimal] = mapped_column(
        Numeric(6, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Price variance percentage",
    )
    quantity_variance_pct: Mapped[Decimal] = mapped_column(
        Numeric(6, 4),
        nullable=False,
        default=Decimal("0"),
        comment="Quantity variance percentage",
    )

    # Matched quantities
    invoice_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        comment="Invoiced quantity",
    )
    po_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        comment="PO quantity",
    )
    invoice_unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        comment="Invoice unit price",
    )
    po_unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        comment="PO unit price",
    )

    # Match type (how was this matched)
    match_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="exact",
        comment="Match type: exact, fuzzy, learned, manual",
    )
    match_criteria: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Criteria that matched (e.g., SKU, description, supplier)",
    )

    # User confirmation
    is_confirmed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether user confirmed this match",
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Confirmation timestamp",
    )
    confirmed_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="User who confirmed",
    )

    # Learning promotion
    is_promoted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Whether promoted to learned reference",
    )
    promoted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Promotion timestamp",
    )
    promotion_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of times promoted",
    )

    # Usage tracking
    use_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of times used for matching",
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last usage timestamp",
    )
    last_match_result: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Last match result: success, failed",
    )

    # Source tracking
    source_invoice_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Source invoice date",
    )
    source_match_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Date when match was made",
    )

    # Relationships
    invoice_line: Mapped["InvoiceLine | None"] = relationship(
        "InvoiceLine",
        foreign_keys=[invoice_line_id],
    )

    @property
    def is_usable(self) -> bool:
        """Check if this cross-reference is usable for matching."""
        return self.is_confirmed or self.match_confidence >= 90.0

    def increment_use(self, success: bool = True) -> None:
        """Increment usage counter."""
        self.use_count += 1
        self.last_used_at = datetime.utcnow()
        self.last_match_result = "success" if success else "failed"

    def promote(self) -> bool:
        """
        Promote to learned reference.
        
        Returns:
            bool: True if promoted, False if already promoted
        """
        if not self.is_promoted:
            self.is_promoted = True
            self.promoted_at = datetime.utcnow()
            self.promotion_count += 1
            return True
        self.promotion_count += 1
        return False

    def confirm(self, user: str | None = None) -> None:
        """Mark as confirmed by user."""
        self.is_confirmed = True
        self.confirmed_at = datetime.utcnow()
        self.confirmed_by = user

    def __repr__(self) -> str:
        return f"<CrossRef(id={self.id}, sku={self.sku}, confidence={self.match_confidence})>"
