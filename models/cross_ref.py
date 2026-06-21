// models/cross_ref.py
"""CrossRef SQLAlchemy model.

Learning loop table for confirmed matches and supplier/item relationships.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin


class CrossRef(Base, UUIDMixin, TimestampMixin):
    """Cross Reference model.

    Learning loop table that stores confirmed matches for future reference.
    Used to promote frequently matched supplier/item relationships.
    """

    __tablename__ = "cross_ref"
    __table_args__ = (
        Index("ix_cross_ref_vendor_code", "vendor_code"),
        Index("ix_cross_ref_po_item_code", "po_item_code"),
        Index("ix_cross_ref_invoice_item_code", "invoice_item_code"),
        Index("ix_cross_ref_supplier_confidence", "supplier_confidence"),
        Index("ix_cross_ref_promoted", "is_promoted"),
        UniqueConstraint(
            "vendor_code",
            "po_item_code",
            "invoice_item_code",
            name="uq_cross_ref_vendor_po_invoice_item",
        ),
        {"schema": None},
    )

    # Vendor Info
    vendor_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=True)

    # Item Code Mapping
    po_item_code: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    po_item_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    invoice_item_code: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    invoice_item_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Match Statistics
    match_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confirmation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rejection_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Score Data
    avg_match_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("0.00"))
    last_match_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    last_match_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Confidence & Promotion
    supplier_confidence: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    is_promoted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    promoted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    promoted_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Auto-match Settings
    auto_match_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    auto_match_threshold: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("80.00")
    )

    # Reference Documents
    last_po_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_invoice_number: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<CrossRef {self.vendor_code}: {self.po_item_code} -> {self.invoice_item_code}>"

    @property
    def success_rate(self) -> float:
        """Calculate confirmation success rate."""
        total = self.confirmation_count + self.rejection_count
        if total == 0:
            return 0.0
        return (self.confirmation_count / total) * 100

    def confirm_match(self, score: float) -> None:
        """Record a confirmed match.

        Args:
            score: The match score for this confirmation.
        """
        self.confirmation_count += 1
        self.match_count += 1
        self.last_match_score = Decimal(str(score))
        self.last_match_date = datetime.now(timezone.utc)
        self._update_avg_score(score)

    def reject_match(self) -> None:
        """Record a rejected match."""
        self.rejection_count += 1
        self.match_count += 1
        self.last_match_date = datetime.now(timezone.utc)

    def _update_avg_score(self, new_score: float) -> None:
        """Update average score with new score.

        Args:
            new_score: New score to incorporate into average.
        """
        total = self.avg_match_score * (self.match_count - 1) + new_score
        self.avg_match_score = Decimal(str(total / self.match_count))

    def should_promote(self, min_confirmations: int = 3) -> bool:
        """Check if this cross-reference should be promoted.

        Args:
            min_confirmations: Minimum confirmations required.

        Returns:
            True if should be promoted based on criteria.
        """
        if self.is_promoted:
            return False

        return (
            self.confirmation_count >= min_confirmations
            and self.success_rate >= 80.0
            and self.avg_match_score >= Decimal("80.00")
        )

    def promote(self, promoted_by: str | None = None) -> None:
        """Promote this cross-reference to high confidence.

        Args:
            promoted_by: User ID or name that promoted this reference.
        """
        self.is_promoted = True
        self.promoted_at = datetime.now(timezone.utc)
        self.promoted_by = promoted_by
        self.supplier_confidence = "high"
        self.auto_match_threshold = Decimal("70.00")
