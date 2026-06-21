// models/cross_ref.py
"""CrossRef SQLAlchemy model.

Stores confirmed matches for the learning loop, enabling
the system to improve matching accuracy over time.
"""

import uuid
from decimal import Decimal

from sqlalchemy import (
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import ExceptionType, MatchConfidence


class CrossRef(Base, UUIDMixin, TimestampMixin):
    """Cross-reference table for confirmed matches.

    Acts as the learning loop, storing verified matches
    to improve future matching accuracy.
    """

    __tablename__ = "cross_ref"
    __table_args__ = (
        Index("ix_cross_ref_invoice_id", "invoice_id"),
        Index("ix_cross_ref_po_id", "po_id"),
        Index("ix_cross_ref_dn_id", "dn_id"),
        Index("ix_cross_ref_match_type", "match_type"),
        Index("ix_cross_ref_confidence", "confidence"),
        Index("ix_cross_ref_created_at", "created_at"),
        Index("ix_cross_ref_sku", "sku"),
        Index("ix_cross_ref_vendor_id", "vendor_id"),
        UniqueConstraint(
            "invoice_id",
            "invoice_line_id",
            "po_id",
            "po_line_id",
            name="uq_invoice_po_line_combo",
        ),
    )

    # Invoice Reference
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Matched invoice ID",
    )
    invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="CASCADE"),
        nullable=True,
        doc="Matched invoice line ID",
    )
    invoice_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Invoice number (denormalized)",
    )
    invoice_date: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        doc="Invoice date (denormalized)",
    )
    invoice_quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        doc="Invoiced quantity (denormalized)",
    )
    invoice_unit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        doc="Invoiced unit price (denormalized)",
    )

    # Purchase Order Reference
    po_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Matched purchase order ID",
    )
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        doc="Matched purchase order line ID",
    )
    po_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="PO number (denormalized)",
    )
    po_date: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        doc="PO date (denormalized)",
    )
    po_quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        doc="PO ordered quantity (denormalized)",
    )
    po_unit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        doc="PO unit price (denormalized)",
    )

    # Delivery Note Reference
    dn_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Matched delivery note ID",
    )
    dn_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
        doc="Matched delivery note line ID",
    )
    dn_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Delivery note number (denormalized)",
    )
    dn_quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        doc="Delivered quantity (denormalized)",
    )

    # Product Matching
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Matched SKU (denormalized)",
    )
    sku_match_type: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        doc="SKU match type (exact, fuzzy, learned)",
    )
    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Product description (denormalized)",
    )

    # Vendor Reference
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Vendor ID (denormalized)",
    )

    # Match Details
    match_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="three_way",
        doc="Match type (two_way, three_way)",
    )
    confidence: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=MatchConfidence.MEDIUM.value,
        doc="Match confidence level",
    )
    match_score: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=0.0,
        doc="Numeric match score (0-100)",
    )

    # Variances
    price_variance: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        doc="Price variance amount",
    )
    price_variance_pct: Mapped[float | None] = mapped_column(
        Numeric(8, 4),
        nullable=True,
        doc="Price variance percentage",
    )
    quantity_variance: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        doc="Quantity variance",
    )
    quantity_variance_pct: Mapped[float | None] = mapped_column(
        Numeric(8, 4),
        nullable=True,
        doc="Quantity variance percentage",
    )

    # Verification
    verified: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        doc="Whether this match was verified",
    )
    verified_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="User who verified the match",
    )
    verified_at: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        doc="Verification timestamp",
    )

    # Learning Loop Metadata
    source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="auto",
        doc="Match source (auto, manual, corrected)",
    )
    exception_type: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        doc="Exception type if this was a manual resolution",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Notes about the match",
    )

    # Usage Statistics
    usage_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of times this match has been used",
    )
    last_used_at: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        doc="Last usage timestamp",
    )
    success_rate: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=100.0,
        doc="Historical success rate percentage",
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="cross_refs",
    )
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="cross_refs",
    )
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="cross_refs",
    )

    def __repr__(self) -> str:
        return f"<CrossRef {self.invoice_number} -> {self.po_number or 'No PO'}>"
