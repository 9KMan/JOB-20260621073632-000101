// app/models/cross_ref.py
"""Cross Reference model for the learning loop / matching history."""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

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
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import CrossRefStatus


class CrossRef(Base, UUIDMixin, TimestampMixin):
    """
    Cross Reference model for learning and pattern recognition.
    
    Tracks confirmed matches between invoice/PO/DN to improve future matching
    accuracy. Patterns are promoted when confidence thresholds are met.
    """

    __tablename__ = "cross_refs"

    # Product/Vendor identification
    product_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    vendor_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # PO reference (what was ordered)
    po_product_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    po_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    po_unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=False, default="EA")

    # Invoice reference (what was invoiced)
    invoice_product_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    invoice_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    invoice_uom: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # DN reference (what was delivered)
    dn_product_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    dn_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    dn_uom: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Match characteristics
    unit_price_po: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 4), nullable=True)
    unit_price_invoice: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 4), nullable=True)
    unit_price_dn: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 4), nullable=True)

    # Quantity ratio (invoice_qty / po_qty)
    quantity_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6), nullable=True)

    # Match metadata
    match_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    match_decision: Mapped[str] = mapped_column(String(50), nullable=False)

    # Learning tracking
    confirmation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rejection_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[CrossRefStatus] = mapped_column(
        String(20),
        nullable=False,
        default=CrossRefStatus.PENDING,
        index=True,
    )

    # Confidence scoring
    confidence_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )
    is_promoted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    promoted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # First/Last seen tracking
    first_match_date: Mapped[date] = mapped_column(Date, nullable=False)
    last_match_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Associated record IDs (for audit)
    first_invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    first_po_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    first_dn_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    # Active flag
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Table constraints and indexes
    __table_args__ = (
        UniqueConstraint(
            "vendor_id", "product_code", 
            name="uq_cross_ref_vendor_product"
        ),
        Index("ix_cross_ref_vendor", "vendor_id"),
        Index("ix_cross_ref_status_confirmations", "status", "confirmation_count"),
        Index("ix_cross_ref_promoted", "is_promoted", "status"),
    )

    def __repr__(self) -> str:
        return f"<CrossRef(id={self.id}, vendor={self.vendor_id}, product={self.product_code})>"

    def confirm_match(self, match_score: Decimal, match_date: date) -> None:
        """
        Record a successful match confirmation.
        
        Args:
            match_score: The matching score of this confirmation
            match_date: The date of the match
        """
        self.confirmation_count += 1
        self.last_match_date = match_date
        
        # Update running confidence
        total = self.confirmation_count + self.rejection_count
        if total > 0:
            self.confidence_score = Decimal(self.confirmation_count) / Decimal(total)
        
        # Check for promotion
        if self.should_promote():
            self.promote()

    def reject_match(self, rejection_date: date) -> None:
        """
        Record a rejected match.
        
        Args:
            rejection_date: The date of the rejection
        """
        self.rejection_count += 1
        
        # Update running confidence
        total = self.confirmation_count + self.rejection_count
        if total > 0:
            self.confidence_score = Decimal(self.confirmation_count) / Decimal(total)
        
        # Demote if confidence drops too low
        if self.confidence_score < Decimal("0.3"):
            self.demote()

    def should_promote(self) -> bool:
        """Check if this cross-reference should be promoted."""
        from app.core.config import settings
        
        return (
            not self.is_promoted
            and self.confirmation_count >= settings.MIN_CONFIRMATIONS_FOR_PROMOTION
            and self.confidence_score >= Decimal("0.8")
        )

    def promote(self) -> None:
        """Promote this cross-reference to higher confidence."""
        from app.core.config import settings
        
        self.is_promoted = True
        self.status = CrossRefStatus.PROMOTED
        self.promoted_at = datetime.now(timezone.utc)
        # Boost confidence score
        self.confidence_score = min(
            Decimal("1.0"),
            self.confidence_score + Decimal(str(settings.PROMOTION_CONFIDENCE_BOOST))
        )

    def demote(self) -> None:
        """Demote this cross-reference."""
        self.is_promoted = False
        self.status = CrossRefStatus.LEARNING
        self.promoted_at = None
