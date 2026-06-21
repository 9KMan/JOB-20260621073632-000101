// models/cross_ref.py
"""Cross Reference model definition.

This module defines the CrossRef SQLAlchemy model for the learning loop
that stores confirmed matches for future reference.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4

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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class CrossRef(Base):
    """Cross Reference database model.

    Stores confirmed matches for the learning loop. When a match is
    manually confirmed by a user, it's stored here to improve future
    automatic matching.
    """

    __tablename__ = "cross_refs"
    __table_args__ = (
        Index("ix_cross_refs_tenant", "tenant_id"),
        Index("ix_cross_refs_invoice_product", "invoice_vendor_number", "invoice_product_code"),
        Index("ix_cross_refs_po_product", "po_vendor_number", "po_product_code"),
        Index("ix_cross_refs_match_key", "match_key"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # Match key for lookup (hash of product/vendor combination)
    match_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)

    # Invoice reference (source)
    invoice_vendor_number: Mapped[str] = mapped_column(String(50), nullable=False)
    invoice_product_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    invoice_product_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    invoice_unit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 4), nullable=True)

    # PO reference (target)
    po_vendor_number: Mapped[str] = mapped_column(String(50), nullable=False)
    po_product_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    po_product_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    po_unit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 4), nullable=True)

    # Match details
    match_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    last_match_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    avg_match_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    # Price variance tracking
    price_variance_pct: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(6, 2), nullable=True
    )
    avg_price_variance_pct: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(6, 2), nullable=True
    )

    # Confidence and status
    confidence_level: Mapped[str] = mapped_column(String(10), nullable=False, default="LOW")
    is_promoted: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Promotion tracking
    promotion_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    promotion_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    last_promoted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # User confirmation
    confirmed_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Metadata
    source_systems: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Soft delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<CrossRef {self.match_key[:8]}... ({self.match_count} matches)>"

    @property
    def can_promote(self) -> bool:
        """Check if this cross-ref can be promoted to higher confidence."""
        return self.match_count >= self.promotion_threshold and not self.is_promoted

    def calculate_match_key(
        vendor_number: str,
        invoice_product_code: Optional[str],
        po_product_code: Optional[str],
    ) -> str:
        """Generate a match key for product/vendor combination.

        Args:
            vendor_number: The vendor number.
            invoice_product_code: Product code from invoice.
            po_product_code: Product code from PO.

        Returns:
            str: SHA256 hash-based match key.
        """
        import hashlib

        # Normalize product codes
        inv_prod = (invoice_product_code or "").upper().strip()
        po_prod = (po_product_code or "").upper().strip()

        # Create normalized key
        key_parts = f"{vendor_number}:{inv_prod}:{po_prod}"
        return hashlib.sha256(key_parts.encode()).hexdigest()


class MatchException(Base):
    """Match Exception database model.

    Tracks exceptions that occur during the matching process
    and their resolution status.
    """

    __tablename__ = "match_exceptions"
    __table_args__ = (
        Index("ix_match_exceptions_invoice_id", "invoice_id"),
        Index("ix_match_exceptions_status", "status"),
        Index("ix_match_exceptions_exception_type", "exception_type"),
        Index("ix_match_exceptions_tenant_status", "tenant_id", "status"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # References
    invoice_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )
    invoice_line_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("invoice_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Exception details
    exception_type: Mapped[str] = mapped_column(String(30), nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False, default="MEDIUM")

    # Variance details
    expected_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    actual_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    variance_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    variance_percentage: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(6, 2), nullable=True
    )

    # Status and resolution
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="OPEN")
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Review tracking
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    escalated_to: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    # Context
    context_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<MatchException {self.exception_type} - {self.status}>"
