# models/cross_ref.py
"""CrossRef SQLAlchemy model for learning loop/cross-reference data."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import DecisionType


class CrossRef(Base, UUIDMixin, TimestampMixin):
    """Cross Reference model for learning loop and confirmed matches.

    This table stores confirmed matches between Invoice lines and
    PO/DN lines to improve future matching accuracy.
    """

    __tablename__ = "cross_ref"

    # Document References
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Reference to Invoice",
    )
    invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        doc="Reference to Invoice Line",
    )
    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        doc="Reference to Purchase Order",
    )
    purchase_order_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        doc="Reference to PO Line",
    )
    delivery_note_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        doc="Reference to Delivery Note",
    )
    delivery_note_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        doc="Reference to DN Line",
    )

    # Match Details
    match_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="Match type: PO_ONLY, DN_ONLY, PO_DN",
    )
    decision: Mapped[DecisionType] = mapped_column(
        String(20),
        nullable=False,
        doc="Match decision: AUTO_APPROVED, REVIEW, EXCEPTION",
    )

    # Scoring
    matching_score: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        doc="Matching score percentage (0-100)",
    )
    price_match_score: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        doc="Price component score",
    )
    quantity_match_score: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        doc="Quantity component score",
    )
    description_match_score: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        doc="Description match component score",
    )

    # Matched Values
    invoice_quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        doc="Matched invoice quantity",
    )
    invoice_unit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        doc="Matched invoice unit price",
    )
    po_quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        doc="Matched PO quantity",
    )
    po_unit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        doc="Matched PO unit price",
    )
    dn_quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        doc="Matched DN quantity",
    )

    # Learning Data
    product_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        doc="Product code (learned)",
    )
    supplier_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Supplier ID",
    )
    confirmed_price: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        doc="Confirmed/settled unit price",
    )
    confirmed_quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        doc="Confirmed/settled quantity",
    )

    # Promotion tracking
    match_count: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        doc="Number of times this match pattern was used",
    )
    is_promoted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether this is a promoted/high-confidence match",
    )
    confidence_level: Mapped[str] = mapped_column(
        String(20),
        default="LOW",
        nullable=False,
        doc="Confidence level: LOW, MEDIUM, HIGH",
    )

    # User confirmation
    confirmed_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="User who confirmed this match",
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when match was confirmed",
    )

    # Quality tracking
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Additional notes about the match",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether this cross-ref is active",
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="cross_refs",
    )

    __table_args__ = (
        Index("ix_cross_ref_invoice", "invoice_id"),
        Index("ix_cross_ref_po_line", "purchase_order_line_id"),
        Index("ix_cross_ref_dn_line", "delivery_note_line_id"),
        Index("ix_cross_ref_supplier_product", "supplier_id", "product_code"),
        Index("ix_cross_ref_confidence", "confidence_level", "is_active"),
        Index("ix_cross_ref_match_count", "match_count", "is_promoted"),
    )

    def __repr__(self) -> str:
        return f"<CrossRef {self.match_type} - Score: {self.matching_score}>"

    def promote(self) -> None:
        """Promote this cross-reference to high confidence."""
        self.is_promoted = True
        self.confidence_level = "HIGH"
        self.match_count += 1

    def confirm(self, user: str) -> None:
        """Mark this cross-reference as confirmed by user."""
        self.confirmed_by = user
        self.confirmed_at = datetime.now(timezone.utc)
        if self.decision == DecisionType.REVIEW:
            self.decision = DecisionType.AUTO_APPROVED
