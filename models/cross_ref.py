// models/cross_ref.py
"""Cross Reference model definition.

This module defines the CrossRef SQLAlchemy model representing
the learning loop / cross-reference table that stores confirmed
matching relationships for future automation.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.enums import MatchDecisionType

if TYPE_CHECKING:
    from models.invoice import Invoice
    from models.purchase_order import PurchaseOrder


class CrossRef(Base):
    """Cross Reference (Learning Loop) model.

    Stores confirmed matching relationships between invoices and POs
    to enable the learning/promotion system for future automatic matching.

    When a human reviewer confirms a match or overrides a decision,
    this record is created to teach the system for similar cases.

    Attributes:
        id: UUID primary key
        invoice_id: Reference to the invoice
        purchase_order_id: Reference to the purchase order
        po_line_id: Reference to specific PO line (if applicable)
        match_score: The matching score when this was confirmed
        match_decision: The decision made (auto_approved, reviewed, etc.)
        vendor_code: Vendor for quick lookup
        invoice_line_item: Invoice line item description/code
        po_line_item: PO line item description/code
        confirmed_at: When this match was confirmed
        confirmed_by: Who/what confirmed this match
        usage_count: Number of times this cross-reference was used
        is_promoted: Whether this has been promoted to auto-match rules
        is_active: Whether this cross-reference is still valid
        expires_at: When this reference expires (if applicable)
        created_at: Record creation timestamp
        updated_at: Record update timestamp
    """

    __tablename__ = "cross_references"

    # References
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        doc="Reference to the invoice",
    )
    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        doc="Reference to the purchase order",
    )
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("po_lines.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        doc="Reference to specific PO line",
    )

    # Item matching info
    vendor_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Vendor code",
    )
    invoice_line_item: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Invoice line item code/description",
    )
    po_line_item: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="PO line item code/description",
    )

    # Match details
    match_score: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        doc="Matching score (0-100)",
    )
    match_decision: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Match decision made",
    )

    # Price/qty info at time of match
    invoice_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        doc="Invoice amount at match time",
    )
    po_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        doc="PO amount at match time",
    )
    variance_percentage: Mapped[float] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
        doc="Price variance percentage",
    )

    # Confirmation info
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When this match was confirmed",
    )
    confirmed_by: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Who/what confirmed this match",
    )

    # Learning/promotion tracking
    usage_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of times used for matching",
    )
    is_promoted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether promoted to auto-match rules",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether this reference is still valid",
    )

    # Expiration
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Expiration timestamp",
    )

    # Relationships
    invoice: Mapped["Invoice | None"] = relationship(
        "Invoice",
        back_populates="cross_refs",
    )
    purchase_order: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder",
        back_populates="cross_refs",
    )

    # Table indexes
    __table_args__ = (
        Index("ix_cross_ref_vendor", "vendor_code"),
        Index("ix_cross_ref_invoice_po", "invoice_id", "purchase_order_id"),
        Index("ix_cross_ref_items", "invoice_line_item", "po_line_item"),
        Index("ix_cross_ref_active", "is_active", "is_promoted"),
        Index("ix_cross_ref_usage", "usage_count"),
    )

    def __repr__(self) -> str:
        """String representation of CrossRef."""
        return (
            f"<CrossRef(id={self.id}, vendor={self.vendor_code}, "
            f"invoice_item={self.invoice_line_item}, usage={self.usage_count})>"
        )

    def increment_usage(self) -> None:
        """Increment usage count when this reference is used for matching."""
        self.usage_count += 1

    def promote(self) -> None:
        """Promote this cross-reference to auto-match rules."""
        self.is_promoted = True
        self.updated_at = datetime.now(timezone.utc)

    def deactivate(self) -> None:
        """Deactivate this cross-reference."""
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)


# Import uuid
import uuid
