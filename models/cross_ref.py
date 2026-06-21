// models/cross_ref.py
"""CrossRef database model for learning/promotion logic.

Stores learned matches to improve future matching accuracy.
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin
from models.enums import MatchDecision

if TYPE_CHECKING:
    from models.invoice import InvoiceLine
    from models.purchase_order import PurchaseOrderLine


class CrossRef(Base, TimestampMixin):
    """Cross-reference model for learned matches.

    Stores confirmed matches between PO lines and invoice lines
    to improve future matching accuracy through promotion.
    """

    __tablename__ = "cross_ref"
    __table_args__ = (
        Index("ix_cross_ref_po_line_id", "po_line_id"),
        Index("ix_cross_ref_invoice_line_id", "invoice_line_id"),
        Index("ix_cross_ref_vendor_product", "vendor_number", "product_sku"),
        Index("ix_cross_ref_match_score", "match_score"),
        UniqueConstraint(
            "po_line_id",
            "invoice_line_id",
            name="uq_cross_ref_po_invoice",
        ),
        {"schema": "public"},
    )

    # Foreign keys
    po_line_id: Mapped[str] = mapped_column(String(36), nullable=False)
    invoice_line_id: Mapped[str] = mapped_column(String(36), nullable=True)

    # Product/vendor context
    vendor_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    product_sku: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    product_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    po_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    invoice_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Match details
    match_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    match_decision: Mapped[str] = mapped_column(String(30), nullable=False)
    is_auto_matched: Mapped[bool] = mapped_column(Boolean, default=False)

    # Quantity information
    po_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    invoice_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    matched_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)

    # Price information
    po_unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    invoice_unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    price_variance: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)

    # Confidence and learning
    confidence_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    use_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_promoted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_rejected: Mapped[bool] = mapped_column(Boolean, default=False)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # User confirmation
    confirmed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_user_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Metadata
    match_criteria: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Expiry for learned patterns
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_expired: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    def promote(self) -> None:
        """Promote this cross-reference to higher confidence."""
        if self.confidence_level < 5:
            self.confidence_level += 1
            self.is_promoted = True

    def demote(self) -> None:
        """Demote this cross-reference."""
        if self.confidence_level > 0:
            self.confidence_level -= 1

    def confirm(self, user_id: str) -> None:
        """Mark this cross-reference as user-confirmed."""
        self.is_user_confirmed = True
        self.confirmed_by = user_id
        self.confirmed_at = datetime.utcnow()
        self.is_auto_matched = False

    def reject(self, reason: str) -> None:
        """Reject this cross-reference."""
        self.is_rejected = True
        self.rejection_reason = reason

    def increment_use(self) -> None:
        """Increment the use count."""
        self.use_count += 1

    def __repr__(self) -> str:
        return f"<CrossRef {self.vendor_number}/{self.product_sku} score={self.match_score}>"
