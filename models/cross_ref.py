# models/cross_ref.py
"""Cross-Reference (Learning Loop) SQLAlchemy model.

Stores learned patterns from confirmed matches for future matching.
"""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from models.enums import CrossRefType, LearningStatus

if TYPE_CHECKING:
    pass


class CrossRef(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Cross-Reference (Learning) model.

    Stores learned patterns from confirmed matches. When a match is
    confirmed multiple times, the pattern is promoted to this table
    for future automatic matching.
    """

    __tablename__ = "cross_ref"
    __table_args__ = (
        Index("ix_cross_ref_ref_type", "ref_type"),
        Index("ix_cross_ref_vendor_number", "vendor_number"),
        Index("ix_cross_ref_product_number", "product_number"),
        Index("ix_cross_ref_po_number", "po_number"),
        Index("ix_cross_ref_status", "status"),
        Index("ix_cross_ref_confirmed_count", "confirmed_count"),
        {"schema": None},
    )

    # Reference type
    ref_type: Mapped[CrossRefType] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    # Vendor info
    vendor_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    vendor_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Product info
    product_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    product_description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # PO reference
    po_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )
    po_line_number: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # Learned values
    unit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
    )
    quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
    )
    tax_code: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    # Pricing tolerance learned
    price_tolerance_low: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0"),
    )
    price_tolerance_high: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0"),
    )

    # Quantity tolerance learned
    qty_tolerance_low: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0"),
    )
    qty_tolerance_high: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0"),
    )

    # Learning stats
    confirmed_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        index=True,
    )
    rejected_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    last_confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Status and promotion
    status: Mapped[LearningStatus] = mapped_column(
        String(20),
        nullable=False,
        default=LearningStatus.ACTIVE,
        index=True,
    )
    is_promoted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )
    promoted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Validity period
    valid_from: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today,
    )
    valid_until: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Confidence score (calculated from confirmed/rejected ratio)
    confidence_score: Mapped[float] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0"),
    )

    def __repr__(self) -> str:
        return f"<CrossRef {self.ref_type}:{self.vendor_number}:{self.product_number}>"

    def update_confidence(self) -> None:
        """Update confidence score based on confirmed/rejected ratio."""
        total = self.confirmed_count + self.rejected_count
        if total == 0:
            self.confidence_score = 0.0
        else:
            self.confidence_score = float(self.confirmed_count / total)

    def confirm_match(self) -> None:
        """Record a confirmed match."""
        self.confirmed_count += 1
        self.last_confirmed_at = datetime.now(timezone.utc)
        self.update_confidence()

    def reject_match(self) -> None:
        """Record a rejected match."""
        self.rejected_count += 1
        self.update_confidence()

    @property
    def is_expired(self) -> bool:
        """Check if the cross-reference is expired."""
        if self.valid_until is None:
            return False
        return date.today() > self.valid_until

    @property
    def should_promote(self) -> bool:
        """Check if should be promoted based on confirmation count."""
        return self.confirmed_count >= 3 and not self.is_promoted
