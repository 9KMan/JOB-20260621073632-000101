# models/cross_ref.py
"""Cross-reference table for learning/promotion logic."""

import uuid
from decimal import Decimal
from datetime import date

from sqlalchemy import (
    Date,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CrossRef(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Learning loop / cross-reference table.
    
    Stores confirmed matches for future reference and automatic promotion.
    This enables the system to learn from human decisions and improve
    matching accuracy over time.
    """

    __tablename__ = "cross_ref"

    # Product/Service Identification
    vendor_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    vendor_product_code: Mapped[str] = mapped_column(String(100), nullable=False)
    vendor_product_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Reference Product (internal catalog)
    internal_product_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    internal_product_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Reference PO Line
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    # Match Metrics
    match_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    avg_match_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    last_match_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Promotion
    is_promoted: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    promoted_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    promoted_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        default="active",
        nullable=False,
        index=True,
    )

    # Validation
    min_match_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    max_match_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    # Relationships
    po_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        foreign_keys=[po_line_id],
    )

    __table_args__ = (
        UniqueConstraint(
            "vendor_id",
            "vendor_product_code",
            name="uq_cross_ref_vendor_product",
        ),
        Index("ix_cross_ref_vendor_internal", "vendor_id", "internal_product_code"),
    )
