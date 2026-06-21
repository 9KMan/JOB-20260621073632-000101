// models/cross_ref.py
"""CrossRef SQLAlchemy model for learning loop/cross-reference tracking."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

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

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from models.enums import LearningStatus, MatchType


class CrossRef(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Cross-Reference table for learning loop and match promotion.

    This table stores learned associations between invoice line attributes
    and purchase order line attributes, enabling the system to improve
    matching accuracy over time.
    """

    __tablename__ = "cross_ref"
    __table_args__ = (
        Index("ix_cross_ref_invoice_sku", "invoice_sku"),
        Index("ix_cross_ref_po_sku", "po_sku"),
        Index("ix_cross_ref_invoice_product_code", "invoice_product_code"),
        Index("ix_cross_ref_po_product_code", "po_product_code"),
        Index("ix_cross_ref_vendor_number", "vendor_number"),
        Index("ix_cross_ref_status", "status"),
        Index("ix_cross_ref_confidence_score", "confidence_score"),
    )

    # Vendor
    vendor_number: Mapped[str] = mapped_column(String(50), nullable=False)
    vendor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Invoice attributes
    invoice_sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    invoice_product_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    invoice_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # PO attributes
    po_sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    po_product_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    po_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Match details
    match_type: Mapped[str] = mapped_column(
        String(20),
        default=MatchType.LEARNED.value,
        nullable=False,
    )
    match_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )

    # Learning metrics
    confidence_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.5000"),
        nullable=False,
    )
    confirmation_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    rejection_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    last_confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_rejected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default=LearningStatus.PENDING.value,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Source references
    source_invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Metadata
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def confirm(self) -> None:
        """Confirm this cross-reference mapping."""
        self.confirmation_count += 1
        self.last_confirmed_at = datetime.now()
        self.update_confidence()

    def reject(self) -> None:
        """Reject this cross-reference mapping."""
        self.rejection_count += 1
        self.last_rejected_at = datetime.now()
        self.update_confidence()

    def update_confidence(self) -> None:
        """Update confidence score based on confirmations/rejections."""
        total = self.confirmation_count + self.rejection_count
        if total > 0:
            self.confidence_score = Decimal(self.confirmation_count) / Decimal(total)
        if self.confidence_score >= Decimal("0.9"):
            self.status = LearningStatus.PROMOTED.value
        elif self.confidence_score <= Decimal("0.2"):
            self.status = LearningStatus.DEMOTED.value

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "vendor_number": self.vendor_number,
            "invoice_sku": self.invoice_sku,
            "invoice_product_code": self.invoice_product_code,
            "po_sku": self.po_sku,
            "po_product_code": self.po_product_code,
            "match_score": float(self.match_score),
            "confidence_score": float(self.confidence_score),
            "status": self.status,
            "is_active": self.is_active,
        }

    def __repr__(self) -> str:
        return f"<CrossRef {self.invoice_sku} -> {self.po_sku} ({self.confidence_score})>"
