# models/cross_ref.py
"""CrossRef SQLAlchemy model for learning/promotion logic."""

import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from models.base import BaseModel
from models.enums import LearningStatus, MatchType


class CrossRef(BaseModel):
    """
    Cross-Reference model for the learning loop.
    
    Stores learned/promoted matches between invoice lines and PO lines
    to improve future matching accuracy.
    
    Attributes:
        invoice_vendor_id: Vendor ID pattern for invoices
        invoice_sku: SKU pattern from invoice
        invoice_description: Description pattern from invoice
        po_vendor_id: Matching vendor ID for PO
        po_sku: SKU pattern from PO
        po_description: Description pattern from PO
        match_count: Number of times this cross-reference was used
        success_count: Number of successful matches using this rule
        success_rate: Calculated success rate
        status: Learning status (pending, learned, promoted, rejected)
        confidence: Confidence level
        expires_at: When this entry expires
        is_active: Whether this rule is currently active
    """

    __tablename__ = "cross_refs"

    # Invoice pattern fields
    invoice_vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Vendor ID pattern from invoice",
    )
    invoice_sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="SKU pattern from invoice (may be partial)",
    )
    invoice_description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Description pattern from invoice",
    )

    # PO pattern fields
    po_vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Matching vendor ID for PO",
    )
    po_sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="SKU pattern from PO",
    )
    po_description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Description pattern from PO",
    )

    # Matching statistics
    match_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of times this cross-reference was used",
    )
    success_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of successful matches",
    )
    success_rate: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Success rate percentage",
    )

    # Status and lifecycle
    status: Mapped[LearningStatus] = mapped_column(
        String(20),
        nullable=False,
        default=LearningStatus.PENDING,
        index=True,
        doc="Current learning status",
    )
    confidence: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="medium",
        doc="Confidence level (high, medium, low)",
    )
    match_type: Mapped[MatchType] = mapped_column(
        String(20),
        nullable=False,
        default=MatchType.LEARNED,
        doc="Type of match (exact, fuzzy, learned, manual)",
    )

    # Expiration
    expires_at: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Expiration date",
    )
    last_used_at: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Last time this rule was used",
    )

    # Activation
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        doc="Whether this rule is currently active",
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether this rule has been manually verified",
    )

    # Quality metrics
    avg_match_score: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Average match score when used",
    )
    false_positive_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of false positives detected",
    )

    # Source tracking
    source_invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
        doc="Source invoice that created this rule",
    )
    source_po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        doc="Source PO line that created this rule",
    )

    # Promotion tracking
    promoted_at: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="When this rule was promoted",
    )
    promotion_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Reason for promotion",
    )

    __table_args__ = (
        UniqueConstraint(
            "invoice_vendor_id",
            "invoice_sku",
            "po_vendor_id",
            "po_sku",
            name="uq_cross_ref_invoice_po_pattern",
        ),
        Index("ix_cross_ref_invoice_pattern", "invoice_vendor_id", "invoice_sku"),
        Index("ix_cross_ref_po_pattern", "po_vendor_id", "po_sku"),
        Index("ix_cross_ref_status_active", "status", "is_active"),
    )

    @classmethod
    def calculate_expiry(cls, match_count: int, success_rate: float) -> date:
        """Calculate expiry date based on usage."""
        if success_rate >= 95 and match_count >= 10:
            return date.today() + timedelta(days=365)
        elif success_rate >= 80 and match_count >= 5:
            return date.today() + timedelta(days=180)
        else:
            return date.today() + timedelta(days=90)

    def update_success_rate(self) -> None:
        """Update success rate based on current counts."""
        if self.match_count > 0:
            self.success_rate = (self.success_count / self.match_count) * 100
        else:
            self.success_rate = 0.0

    def __repr__(self) -> str:
        return (
            f"<CrossRef(id={self.id}, status={self.status}, "
            f"success_rate={self.success_rate}%)>"
        )
