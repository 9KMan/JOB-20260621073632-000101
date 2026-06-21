# models/cross_ref.py
"""CrossRef SQLAlchemy model.

Learning loop / cross-reference table for confirmed matches.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin


class CrossRef(Base, UUIDMixin, TimestampMixin):
    """Cross-reference table for learned matches.

    Stores confirmed invoice-to-PO-line matches to improve future matching.
    Used by the learning service to promote matches and improve accuracy.

    Attributes:
        source_type: Type of source document (invoice, delivery_note)
        source_id: ID of the source document
        source_line_id: ID of the source line item
        source_sku: SKU from source line
        source_description: Description from source line
        target_type: Type of target document (purchase_order, etc.)
        target_id: ID of the target document
        target_line_id: ID of the target PO line
        target_sku: SKU from target line
        target_description: Description from target line
        vendor_id: Vendor identifier (for validation)
        match_count: Number of times this match was confirmed
        last_match_date: Last time this match was confirmed
        confidence_score: Calculated confidence score
        is_promoted: Whether this match has been promoted
        is_active: Whether this cross-reference is active
        metadata: Additional JSON metadata
    """

    __tablename__ = "cross_refs"

    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        nullable=False,
        index=True,
    )
    source_line_id: Mapped[uuid.UUID | None] = mapped_column(
        nullable=True,
        index=True,
    )
    source_sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    source_description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    target_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        nullable=False,
        index=True,
    )
    target_line_id: Mapped[uuid.UUID | None] = mapped_column(
        nullable=True,
        index=True,
    )
    target_sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    target_description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    vendor_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    match_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    first_match_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    last_match_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    confidence_score: Mapped[float] = mapped_column(
        nullable=False,
        default=0.5,
    )
    is_promoted: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )
    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    metadata_json: Mapped[dict | None] = mapped_column(
        nullable=True,
    )

    __table_args__ = (
        Index("ix_cross_ref_lookup", "source_type", "source_sku", "vendor_id"),
        Index("ix_cross_ref_target_lookup", "target_type", "target_sku", "vendor_id"),
        UniqueConstraint(
            "source_line_id",
            "target_line_id",
            name="uq_cross_ref_lines",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<CrossRef {self.source_type}:{self.source_sku} -> "
            f"{self.target_type}:{self.target_sku} "
            f"(count={self.match_count})>"
        )

    def increment_match(self, match_date: date) -> None:
        """Increment match count and update last match date.

        Args:
            match_date: Date of the new match
        """
        self.match_count += 1
        self.last_match_date = match_date
        self._update_confidence()

    def _update_confidence(self) -> None:
        """Update confidence score based on match count."""
        # Simple confidence algorithm: log-based scaling
        # More matches = higher confidence, but with diminishing returns
        import math

        self.confidence_score = min(1.0, 0.5 + (math.log(self.match_count + 1) / 10))

    def promote(self) -> None:
        """Promote this cross-reference to high confidence."""
        self.is_promoted = True
        self.confidence_score = 1.0

    def deactivate(self) -> None:
        """Deactivate this cross-reference."""
        self.is_active = False
