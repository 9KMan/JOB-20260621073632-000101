# models/cross_ref.py
"""Cross-reference model for learning loop / pattern learning."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import MatchDecision, MatchStatus


class CrossRef(Base, UUIDMixin, TimestampMixin):
    """
    Cross-reference table for learning loop functionality.
    
    Stores confirmed matches between invoice/PO/DN combinations
    to improve future matching accuracy through pattern recognition.
    """

    __tablename__ = "cross_refs"

    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    purchase_order_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Vendor matching
    vendor_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Product matching
    product_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    product_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Price learning
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    price_deviation: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False, default=Decimal("0"))
    
    # Match metrics
    match_score: Mapped[float] = mapped_column(Float, nullable=False)
    match_decision: Mapped[str] = mapped_column(String(30), nullable=False)
    
    # Usage tracking
    use_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default=MatchStatus.CONFIRMED.value,
        nullable=False,
        index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_promoted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Confirmation
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    confirmed_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Validation
    last_validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    validation_notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="cross_refs"
    )

    __table_args__ = (
        Index("ix_cross_ref_vendor_product", "vendor_code", "product_code"),
        Index("ix_cross_ref_price_range", "unit_price", "price_deviation"),
        Index("ix_cross_ref_active", "is_active", "status"),
    )

    @property
    def success_rate(self) -> float:
        """Calculate the success rate of this cross-reference."""
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return (self.success_count / total) * 100

    @property
    def is_trusted(self) -> bool:
        """Check if this cross-reference is trusted (high success rate, high use count)."""
        return self.success_rate >= 90.0 and self.use_count >= 10

    def record_success(self) -> None:
        """Record a successful use of this cross-reference."""
        self.use_count += 1
        self.success_count += 1

    def record_failure(self) -> None:
        """Record a failed use of this cross-reference."""
        self.use_count += 1
        self.failure_count += 1

    def promote(self) -> None:
        """Promote this cross-reference to a trusted pattern."""
        self.is_promoted = True
        self.is_active = True


from models.purchase_order import PurchaseOrder, PurchaseOrderLine
