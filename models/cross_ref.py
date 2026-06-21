# models/cross_ref.py
"""Cross Reference model for the learning loop / AI suggestions."""

import uuid
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Float,
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


class CrossRef(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Cross Reference model for learning loop.
    
    Stores learned associations between invoice items and PO/DN items
    to improve future matching accuracy.
    """
    
    __tablename__ = "cross_ref"
    __table_args__ = (
        Index("ix_cross_ref_vendor_id", "vendor_id"),
        Index("ix_cross_ref_sku", "sku"),
        Index("ix_cross_ref_po_line_id", "po_line_id"),
        Index("ix_cross_ref_is_promoted", "is_promoted"),
        Index("ix_cross_ref_match_count", "match_count"),
    )
    
    # Vendor Context
    vendor_id: Mapped[str] = mapped_column(String(100), nullable=False)
    vendor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Product Identification (fuzzy matching keys)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    vendor_sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # PO Line Reference
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Learned Values
    learned_unit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
    )
    learned_quantity_multiplier: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 6),
        nullable=True,
    )
    
    # Match Statistics
    match_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_match_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    avg_match_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    last_match_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_matched_at: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    
    # Promotion Status
    is_promoted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    promoted_at: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    
    # Confidence
    confidence_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    
    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Soft Delete
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
