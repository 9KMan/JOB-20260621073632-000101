// models/cross_ref.py
"""CrossRef and learning loop SQLAlchemy models.

The cross-reference table stores confirmed match patterns
for the learning loop to improve future matching accuracy.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.enums import MatchConfirmation


class CrossRef(Base):
    """Cross-reference model for learning loop.

    Stores confirmed match patterns between:
    - Vendor + SKU
    - Vendor + PO line description
    - Similar products across vendors

    This enables the system to learn and improve matching
    accuracy over time.
    """

    __tablename__ = "cross_ref"
    __table_args__ = (
        UniqueConstraint(
            ["vendor_code", "sku", "po_description_hash"],
            name="uq_cross_ref_vendor_sku_description",
        ),
        Index("ix_cross_ref_vendor_code", "vendor_code"),
        Index("ix_cross_ref_sku", "sku"),
        Index("ix_cross_ref_confirmation", "confirmation"),
        Index("ix_cross_ref_match_count", "match_count"),
    )

    # Identification
    vendor_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Product matching fields
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    sku_normalized: Mapped[str | None] = mapped_column(String(100), nullable=True)
    po_description: Mapped[str] = mapped_column(String(500), nullable=False)
    po_description_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    po_description_normalized: Mapped[str] = mapped_column(String(500), nullable=True)

    # Price information
    unit_price: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    price_tolerance_percent: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=5.0,
    )

    # Learning statistics
    match_count: Mapped[int] = mapped_column(default=0, nullable=False)
    total_match_score: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)
    avg_match_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0)

    # Confirmation and status
    confirmation: Mapped[MatchConfirmation] = mapped_column(
        MatchConfirmation,
        default=MatchConfirmation.PENDING,
        nullable=False,
    )
    confirmation_source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Quality metrics
    success_rate: Mapped[float] = mapped_column(Numeric(5, 4), default=0.0)
    false_positive_count: Mapped[int] = mapped_column(default=0)

    # Metadata
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_matched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def update_score(self, new_score: float) -> None:
        """Update learning statistics with a new match score.

        Args:
            new_score: The match score from a confirmed match (0-100).
        """
        self.match_count += 1
        self.total_match_score += new_score
        self.avg_match_score = self.total_match_score / self.match_count
        self.last_matched_at = datetime.now()

    def confirm(self, source: str = "manual") -> None:
        """Mark this cross-reference as confirmed.

        Args:
            source: Source of confirmation (manual, auto, erp).
        """
        self.confirmation = MatchConfirmation.CONFIRMED
        self.confirmation_source = source
        self.confirmed_at = datetime.now()

    def reject(self) -> None:
        """Mark this cross-reference as rejected."""
        self.confirmation = MatchConfirmation.REJECTED
        self.false_positive_count += 1

    def calculate_quality_score(self) -> float:
        """Calculate a quality score for this cross-reference.

        Returns:
            Quality score between 0 and 100.
        """
        if self.match_count == 0:
            return 0.0

        # Factors: confirmation status, match count, success rate
        confirmation_weight = 0.4
        count_weight = 0.3
        success_weight = 0.3

        confirmation_score = (
            1.0 if self.confirmation == MatchConfirmation.CONFIRMED else 0.5
        )
        count_score = min(self.match_count / 10, 1.0)  # Cap at 10 matches
        success_score = 1.0 - min(self.false_positive_count / max(self.match_count, 1), 1.0)

        return (
            confirmation_score * confirmation_weight
            + count_score * count_weight
            + success_score * success_weight
        ) * 100

    def __repr__(self) -> str:
        return (
            f"<CrossRef {self.vendor_code}:{self.sku or 'NO_SKU'} "
            f"({self.match_count} matches, {self.confirmation.value})>"
        )


# Import at bottom to avoid circular imports
from models.purchase_order import PurchaseOrderLine
