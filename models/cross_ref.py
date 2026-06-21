# models/cross_ref.py
"""CrossRef SQLAlchemy model for learning/promotion logic.

Stores confirmed matches between invoice lines, PO lines, and delivery note lines.
Used for the learning loop to improve future match accuracy.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import ExceptionStatus, ExceptionType, MatchConfidence

if TYPE_CHECKING:
    from models.delivery_note import DeliveryNoteLine
    from models.invoice import InvoiceLine
    from models.purchase_order import PurchaseOrderLine


class CrossRef(Base, UUIDMixin, TimestampMixin):
    """Cross-reference table for learned matches.

    Stores confirmed matches between document lines to build a learning
    database that improves future match accuracy.

    Attributes:
        invoice_line_id: Reference to invoice line
        po_line_id: Reference to PO line
        dn_line_id: Optional reference to delivery note line
        match_type: Type of match (exact, fuzzy, manual)
        confidence: Match confidence level
        price_variance: Price difference percentage
        quantity_variance: Quantity difference percentage
        is_promoted: Whether this match has been promoted as a rule
        promotion_count: Number of times this match has been used
        last_used_at: Last time this match was applied
        confirmed_by: User who confirmed this match
        confirmed_at: When the match was confirmed
    """

    __tablename__ = "cross_refs"

    # Line references
    invoice_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "invoice_lines.id",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "purchase_order_lines.id",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    dn_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "delivery_note_lines.id",
            ondelete="SET NULL",
            onupdate="CASCADE",
        ),
        nullable=True,
        index=True,
    )

    # Match details
    match_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="manual",
    )
    confidence: Mapped[MatchConfidence] = mapped_column(
        Enum(MatchConfidence, name="match_confidence"),
        nullable=False,
        default=MatchConfidence.LOW,
    )

    # Variance tracking
    price_variance_pct: Mapped[Decimal] = mapped_column(
        Numeric(10, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )
    quantity_variance_pct: Mapped[Decimal] = mapped_column(
        Numeric(10, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )
    amount_variance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Matched values
    matched_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    # Score
    match_score: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )

    # Learning/promotion
    is_promoted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    promotion_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    usage_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
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

    # Confirmation
    is_confirmed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    confirmed_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )

    # Exception info (if this came from an exception resolution)
    exception_type: Mapped[ExceptionType | None] = mapped_column(
        Enum(ExceptionType, name="exception_type", create_type=False),
        nullable=True,
    )
    exception_status: Mapped[ExceptionStatus | None] = mapped_column(
        Enum(ExceptionStatus, name="exception_status", create_type=False),
        nullable=True,
    )

    # Relationships
    invoice_line: Mapped["InvoiceLine"] = relationship(
        "InvoiceLine",
        back_populates="cross_refs",
    )
    po_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        back_populates="cross_refs",
    )
    dn_line: Mapped["DeliveryNoteLine | None"] = relationship(
        "DeliveryNoteLine",
        back_populates="cross_refs",
    )

    __table_args__ = (
        UniqueConstraint(
            "invoice_line_id",
            "po_line_id",
            name="uq_cross_ref_invoice_po",
        ),
        Index("ix_cross_ref_promoted", "is_promoted", "promotion_count"),
        Index("ix_cross_ref_confidence", "confidence", "match_score"),
        Index("ix_cross_ref_sku", "po_line_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<CrossRef InvoiceLine:{self.invoice_line_id} "
            f"-> POLine:{self.po_line_id} "
            f"Confidence:{self.confidence.value}>"
        )

    @property
    def success_rate(self) -> float:
        """Calculate success rate for this cross-reference."""
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return (self.success_count / total) * 100

    @property
    def is_high_confidence(self) -> bool:
        """Check if this is a high confidence match."""
        return self.confidence == MatchConfidence.HIGH

    def promote(self) -> None:
        """Promote this cross-reference to a rule."""
        self.is_promoted = True
        self.promotion_count += 1

    def record_usage(self, success: bool = True) -> None:
        """Record usage of this cross-reference."""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
