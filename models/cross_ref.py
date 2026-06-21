// models/cross_ref.py
"""Cross Reference (Learning Loop) SQLAlchemy model."""

from decimal import Decimal
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Boolean,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import DecisionType, MatchConfidence

if TYPE_CHECKING:
    from models.invoice import InvoiceLine
    from models.purchase_order import PurchaseOrderLine
    from models.delivery_note import DeliveryNoteLine


class CrossRef(Base, UUIDMixin, TimestampMixin):
    """
    Cross Reference table for learning/promotion logic.

    This table maintains confirmed matches between invoice lines,
    PO lines, and delivery note lines. It serves as the "learning"
    database for the matching engine, allowing it to:
    - Remember confirmed matches for future auto-matching
    - Track match confidence and accuracy
    - Promote high-confidence matches to auto-approve
    """

    __tablename__ = "cross_ref"
    __table_args__ = (
        Index("ix_cross_ref_invoice_line_id", "invoice_line_id"),
        Index("ix_cross_ref_po_line_id", "po_line_id"),
        Index("ix_cross_ref_dn_line_id", "delivery_note_line_id"),
        Index("ix_cross_ref_supplier_number", "supplier_number"),
        Index("ix_cross_ref_product_code", "product_code"),
        Index("ix_cross_ref_match_count", "match_count"),
        Index("ix_cross_ref_success_rate", "success_rate"),
        Index("ix_cross_ref_promotion_level", "promotion_level"),
        Index("ix_cross_ref_created_at", "created_at"),
        {
            "schema": "public",
        },
    )

    # Invoice line reference
    invoice_line_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("invoice_lines.id", ondelete="SET NULL"),
        nullable=True,
        doc="Invoice line ID",
    )

    # PO line reference
    po_line_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        doc="PO line ID",
    )

    # Delivery note line reference
    delivery_note_line_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
        doc="Delivery note line ID",
    )

    # Key matching fields
    supplier_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Supplier account number",
    )
    supplier_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Supplier name",
    )
    product_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Product or service code",
    )
    product_description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Product description",
    )

    # Match parameters at time of confirmation
    match_unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Confirmed match unit price",
    )
    match_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        doc="Confirmed match quantity",
    )
    unit_of_measure: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        doc="Unit of measure",
    )

    # Learning statistics
    match_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of successful matches",
    )
    success_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of approved matches",
    )
    failure_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of rejected matches",
    )
    success_rate: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=0.0,
        doc="Success rate percentage (0-100)",
    )

    # Promotion level (0=none, 1=low, 2=medium, 3=high)
    promotion_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Promotion level for auto-matching",
    )

    # Decision tracking
    decision_type: Mapped[DecisionType] = mapped_column(
        String(20),
        nullable=False,
        doc="Type of decision made",
    )
    confidence: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=0.0,
        doc="Match confidence score (0-100)",
    )

    # Validation details
    price_match: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether prices matched exactly",
    )
    price_variance_percent: Mapped[float] = mapped_column(
        Numeric(7, 4),
        nullable=False,
        default=0.0,
        doc="Price variance percentage",
    )
    quantity_variance_percent: Mapped[float] = mapped_column(
        Numeric(7, 4),
        nullable=False,
        default=0.0,
        doc="Quantity variance percentage",
    )

    # Date range for promotion
    valid_from: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Start date for promotion validity",
    )
    valid_to: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="End date for promotion validity",
    )

    # Manual override
    is_manual_override: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether this was manually confirmed",
    )
    override_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Reason for manual override",
    )

    # Last used
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Last time this cross ref was used",
    )
    last_invoice_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Last invoice number matched",
    )

    # User tracking
    confirmed_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="User who confirmed this match",
    )

    # Additional metadata
    metadata_json: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="Additional metadata as JSON",
    )

    # Relationships
    invoice_line: Mapped["InvoiceLine | None"] = relationship(
        "InvoiceLine",
        back_populates="cross_refs",
    )
    po_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        back_populates="cross_refs",
    )
    delivery_note_line: Mapped["DeliveryNoteLine | None"] = relationship(
        "DeliveryNoteLine",
        back_populates="cross_refs",
    )

    def __repr__(self) -> str:
        return (
            f"<CrossRef(id={self.id}, supplier={self.supplier_number}, "
            f"product={self.product_code}, count={self.match_count})>"
        )
