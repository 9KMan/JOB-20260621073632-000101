# models/cross_ref.py
"""CrossRef SQLAlchemy model for learning/promotion logic.

Stores confirmed matches for the learning loop to improve future matching.
"""

import uuid
from datetime import date
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
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, UUIDMixin, TimestampMixin
from models.enums import MatchConfidence


class CrossRef(Base, UUIDMixin, TimestampMixin):
    """Cross Reference model for learned matches.
    
    Stores confirmed match patterns to improve future matching accuracy.
    This enables the learning loop to promote low-confidence matches
    to higher confidence when patterns are repeatedly confirmed.
    """
    
    __tablename__ = "cross_ref"
    __table_args__ = (
        Index("ix_xref_vendor_number", "vendor_number"),
        Index("ix_xref_item_number", "item_number"),
        Index("ix_xref_vendor_item_number", "vendor_item_number"),
        Index("ix_xref_po_line_id", "po_line_id"),
        Index("ix_xref_confidence", "confidence"),
        Index("ix_xref_promoted", "is_promoted"),
        Index("ix_xref_created_at", "created_at"),
        {"schema": None},
    )
    
    # Vendor identification
    vendor_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Product matching keys
    item_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    vendor_item_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    
    # PO Line reference (the anchor)
    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    
    # Pricing patterns (learned from confirmed matches)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    price_tolerance_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("5.00"),
    )
    
    # Quantity patterns
    typical_quantity: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 3),
        nullable=True,
    )
    quantity_tolerance_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("10.00"),
    )
    
    # Match confidence
    confidence: Mapped[MatchConfidence] = mapped_column(
        String(20),
        nullable=False,
        default=MatchConfidence.MEDIUM,
        index=True,
    )
    
    # Learning loop tracking
    match_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confirm_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reject_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Promotion tracking
    is_promoted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    promoted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)
    promoted_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Confidence score threshold
    last_match_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    
    # Date patterns
    typical_delivery_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Source tracking
    source_system: Mapped[str] = mapped_column(String(50), nullable=False, default="learning")
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Deactivation
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deactivated_at: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)
    deactivation_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # User attribution
    confirmed_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_confirmed_at: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    po_line: Mapped[Optional["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
    )
    
    def __repr__(self) -> str:
        return f"<CrossRef {self.vendor_number}:{self.item_number} - {self.confidence.value}>"
