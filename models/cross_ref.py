# models/cross_ref.py
"""Cross Reference model for the learning/promotion loop."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, TimestampMixin, UUIDMixin


class CrossRef(TimestampMixin, UUIDMixin, Base):
    """
    Cross Reference table for the learning loop.
    
    Stores confirmed matches and their characteristics to improve
    future matching accuracy through promotion/demotion cycles.
    """
    
    __tablename__ = "cross_ref"
    
    # Entity identifiers
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
    )
    invoice_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    invoice_line_number: Mapped[int | None] = mapped_column(nullable=True)
    
    po_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
    )
    po_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    po_line_number: Mapped[int | None] = mapped_column(nullable=True)
    
    dn_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
    )
    dn_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )
    
    # Vendor matching
    vendor_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    
    # Match characteristics
    match_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        description="Match score at time of confirmation",
    )
    price_variance_pct: Mapped[Decimal] = mapped_column(
        Numeric(10, 4),
        default=Decimal("0"),
        nullable=False,
    )
    quantity_variance_pct: Mapped[Decimal] = mapped_column(
        Numeric(10, 4),
        default=Decimal("0"),
        nullable=False,
    )
    
    # Description similarity
    description_match_type: Mapped[str] = mapped_column(
        String(20),
        default="exact",
        nullable=False,
        description="exact, partial, fuzzy, none",
    )
    description_similarity: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0"),
        nullable=False,
    )
    
    # Learning data
    confirmation_source: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        description="auto_approved, manual_override, exception_resolved",
    )
    confirmed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    confirmed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    
    # Promotion/demotion tracking
    match_count: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    success_count: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    failure_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    success_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("1.0"),
        nullable=False,
    )
    is_promoted: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    is_demoted: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    is_blacklisted: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    blacklist_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Metadata
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    __table_args__ = (
        Index("ix_cross_ref_vendor_po", "vendor_id", "po_number"),
        Index("ix_cross_ref_vendor_invoice", "vendor_id", "invoice_number"),
        Index("ix_cross_ref_success_rate", "success_rate", "match_count"),
        Index("ix_cross_ref_promoted", "is_promoted", "success_rate"),
    )
