# models/cross_ref.py
"""CrossRef SQLAlchemy model.

Stores learned match patterns and confirmed matches for the
learning loop functionality.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import CrossRefType

if TYPE_CHECKING:
    from models.invoice import Invoice, InvoiceLine
    from models.purchase_order import PurchaseOrder, PurchaseOrderLine


class CrossRef(Base, UUIDMixin, TimestampMixin):
    """Cross-reference learning table.

    Stores confirmed matches and learned patterns for future
    automatic matching.
    """

    __tablename__ = "cross_ref"
    __table_args__ = (
        Index("ix_cross_ref_supplier_number", "supplier_number"),
        Index("ix_cross_ref_po_number", "po_number"),
        Index("ix_cross_ref_invoice_number", "invoice_number"),
        Index("ix_cross_ref_sku", "sku"),
        Index("ix_cross_ref_match_type", "match_type"),
        Index("ix_cross_ref_promoted", "promoted"),
        Index("ix_cross_ref_confidence", "confidence"),
    )

    # Reference type
    match_type: Mapped[CrossRefType] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # Supplier information
    supplier_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    supplier_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # PO Reference
    po_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    po_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # Invoice Reference
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
    )
    invoice_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # Line references (for line-level matches)
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Product matching
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    sku_alternate: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    description_match: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Match metrics
    confidence: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    match_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Match dates
    po_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    invoice_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Match confirmation
    confirmed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    confirmed_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Learning/promotion
    promotion_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    promoted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )
    promoted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Usage tracking
    use_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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

    # Notes
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<CrossRef {self.match_type} {self.supplier_number} - {self.po_number}>"

    @property
    def success_rate(self) -> Decimal:
        """Calculate success rate of this match pattern."""
        total = self.success_count + self.failure_count
        if total == 0:
            return Decimal("0.00")
        return Decimal(str(self.success_count)) / Decimal(str(total)) * 100


__all__ = [
    "CrossRef",
]
