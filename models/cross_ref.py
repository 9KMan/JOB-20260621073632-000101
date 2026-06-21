# models/cross_ref.py
"""CrossRef (Learning Loop) SQLAlchemy model."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, BaseMixin
from models.enums import MatchSource


class CrossRef(Base, BaseMixin):
    """Learning Loop / Cross-Reference Table.

    Stores confirmed matches and learned patterns to improve future matching.
    """

    __tablename__ = "cross_ref"
    __table_args__ = (
        Index("ix_cross_ref_vendor_id", "vendor_id"),
        Index("ix_cross_ref_sku", "sku"),
        Index("ix_cross_ref_po_number", "po_number"),
        Index("ix_cross_ref_invoice_number", "invoice_number"),
        Index("ix_cross_ref_is_active", "is_active"),
        Index("ix_cross_ref_match_count", "match_count"),
        Index("ix_cross_ref_last_matched", "last_matched_at"),
        # Composite indexes for common lookups
        Index("ix_cross_ref_vendor_sku", "vendor_id", "sku"),
        Index("ix_cross_ref_vendor_po_invoice", "vendor_id", "po_number", "invoice_number"),
    )

    # Vendor Information
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    vendor_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Product Matching
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    product_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    supplier_part_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # PO Reference
    po_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    po_line_number: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    po_id: Mapped[UUID | None] = mapped_column(
        PG_UUID,
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    po_line_id: Mapped[UUID | None] = mapped_column(
        PG_UUID,
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Invoice Reference
    invoice_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    invoice_id: Mapped[UUID | None] = mapped_column(
        PG_UUID,
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Match Details
    match_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    match_source: Mapped[MatchSource] = mapped_column(
        Enum(MatchSource, name="match_source", create_type=False),
        nullable=False,
        default=MatchSource.MANUAL,
    )

    # Match Statistics
    match_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    last_matched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    first_matched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Confidence and Status
    confidence_score: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("100.00"),
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )
    is_promoted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # Verification
    verified_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Pricing Information (learned from confirmed matches)
    unit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
    )
    quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
    )

    # Additional Data
    metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<CrossRef {self.id} vendor={self.vendor_id} "
            f"sku={self.sku} po={self.po_number} count={self.match_count}>"
        )
