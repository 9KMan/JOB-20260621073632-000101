# models/cross_ref.py
"""Cross-reference learning table for invoice-to-PO matching patterns."""
import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import CrossRefConfidence, CrossRefStatus


class CrossReference(Base, UUIDMixin, TimestampMixin):
    """
    Cross-reference table for learning matching patterns.
    Stores confirmed matches to improve future matching accuracy.
    """

    __tablename__ = "cross_references"
    __table_args__ = (
        Index("ix_cross_references_vendor_id", "vendor_id"),
        Index("ix_cross_references_product_code", "product_code"),
        Index("ix_cross_references_confidence", "confidence"),
        Index("ix_cross_references_status", "status"),
    )

    # Vendor context
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    vendor_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    # Product context
    product_code: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    product_name_pattern: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Matching criteria (learned from confirmed matches)
    po_line_description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    invoice_line_description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    description_match_score: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )

    # Price tolerance (learned)
    price_tolerance_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("5.00"),
    )

    # Quantity tolerance (learned)
    quantity_tolerance_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("10.00"),
    )

    # Confidence and status
    confidence: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=CrossRefConfidence.MEDIUM.value,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=CrossRefStatus.ACTIVE.value,
    )

    # Promotion tracking
    match_count: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )
    success_count: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )
    success_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # First and last match timestamps
    first_match_at: Mapped[Optional[str]] = mapped_column(
        String(19),
        nullable=True,
    )
    last_match_at: Mapped[Optional[str]] = mapped_column(
        String(19),
        nullable=True,
    )
    last_success_at: Mapped[Optional[str]] = mapped_column(
        String(19),
        nullable=True,
    )

    # Source match
    source_invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    source_invoice_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    source_po_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    # Auto-promotion settings
    auto_promote: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    promotion_threshold: Mapped[int] = mapped_column(
        nullable=False,
        default=5,
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    vendor = relationship("Vendor")
