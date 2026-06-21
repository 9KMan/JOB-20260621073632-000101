// models/cross_ref.py
"""CrossReference SQLAlchemy model for learning/promoted matches."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

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
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CrossReference(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Learning loop / cross-reference table for promoted matches.

    When a match is manually confirmed multiple times, it gets promoted
    to this table to enable faster automatic matching in the future.
    """

    __tablename__ = "cross_references"
    __table_args__ = (
        Index("ix_cross_ref_vendor_number", "vendor_number"),
        Index("ix_cross_ref_vendor_part_number", "vendor_part_number"),
        Index("ix_cross_ref_confirmed_count", "confirmed_count"),
        Index(
            "ix_cross_ref_vendor_part",
            "vendor_number",
            "vendor_part_number",
        ),
    )

    # Vendor Information
    vendor_number: Mapped[str] = mapped_column(String(50), nullable=False)
    vendor_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    vendor_part_number: Mapped[str] = mapped_column(String(100), nullable=False)
    internal_part_number: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )

    # Reference Data
    po_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    po_line_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    unit_of_measure: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Learning Stats
    confirmed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    promotion_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_confirmed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_match_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 4), nullable=True
    )

    # Confidence
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Metadata
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<CrossReference {self.vendor_number}:{self.vendor_part_number} "
            f"(confirmed: {self.confirmed_count})>"
        )
