# models/cross_ref.py
"""Cross Reference table for learning loop functionality."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Float,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from models.enums import LearningAction, MatchDecision

if TYPE_CHECKING:
    from models.purchase_order import PurchaseOrder, PurchaseOrderLine
    from models.invoice import Invoice, InvoiceLine


class CrossRef(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Cross Reference table for learning/promotion logic.

    This table stores learned associations between documents and their
    attributes, enabling automatic promotion of patterns to the
    learning loop for future matching.

    Attributes:
        id: UUID primary key
        vendor_id: Vendor identifier
        sku: Product SKU (optional)
        po_line_id: Reference to specific PO line
        invoice_line_id: Reference to specific invoice line
        pattern_key: Composite pattern identifier
        match_count: Number of times this pattern was matched
        confirmation_count: Number of confirmed matches
        rejection_count: Number of rejected matches
        success_rate: Calculated success rate (0-100)
        confidence_score: Overall confidence score
        is_promoted: Whether pattern is promoted to auto-match
        is_active: Whether pattern is currently active
        last_used: Last time this pattern was used
        action: Current learning action
        notes: Pattern notes
        metadata: Additional flexible fields
    """

    __tablename__ = "cross_ref"

    # Core identifiers
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    product_description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # References
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Pattern details
    pattern_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    # Matching history
    match_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    confirmation_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    rejection_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Calculated metrics
    success_rate: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    confidence_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    # Status
    is_promoted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )
    is_learned: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # Timing
    last_used: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    first_match: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_confirmed: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Learning action
    action: Mapped[LearningAction] = mapped_column(
        String(50),
        nullable=False,
        default=LearningAction.LEARNED,
    )

    # Additional details
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Tenant
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    # Relationships
    po_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        foreign_keys=[po_line_id],
    )
    invoice_line: Mapped["InvoiceLine | None"] = relationship(
        "InvoiceLine",
        foreign_keys=[invoice_line_id],
    )

    __table_args__ = (
        Index("ix_cross_ref_vendor_sku", "vendor_id", "sku"),
        Index("ix_cross_ref_pattern_key", "pattern_key"),
        Index("ix_cross_ref_promoted", "is_promoted", "is_active"),
        Index("ix_cross_ref_confidence", "confidence_score", "match_count"),
    )

    def __repr__(self) -> str:
        return (
            f"<CrossRef {self.pattern_key} "
            f"(matches: {self.match_count}, "
            f"confirmed: {self.confirmation_count})>"
        )

    def record_match(
        self,
        confirmed: bool = False,
        decision: MatchDecision | None = None,
    ) -> None:
        """
        Record a match attempt.

        Args:
            confirmed: Whether the match was confirmed
            decision: The matching decision made
        """
        from datetime import datetime, timezone

        self.match_count += 1
        self.last_used = datetime.now(timezone.utc)

        if self.first_match is None:
            self.first_match = self.last_used

        if confirmed or decision == MatchDecision.AUTO_APPROVED:
            self.confirmation_count += 1
            self.last_confirmed = datetime.now(timezone.utc)
        elif decision == MatchDecision.REJECTED:
            self.rejection_count += 1

        self._recalculate_metrics()

    def promote(self) -> None:
        """Promote this pattern to auto-match status."""
        self.is_promoted = True
        self.action = LearningAction.PROMOTED

    def demote(self) -> None:
        """Demote this pattern from auto-match status."""
        self.is_promoted = False
        self.action = LearningAction.DEMOTED

    def deactivate(self) -> None:
        """Deactivate this pattern."""
        self.is_active = False

    def activate(self) -> None:
        """Activate this pattern."""
        self.is_active = True

    def _recalculate_metrics(self) -> None:
        """Recalculate success rate and confidence score."""
        if self.match_count > 0:
            self.success_rate = (self.confirmation_count / self.match_count) * 100

            # Confidence based on match count and success rate
            # More matches = higher confidence, but with diminishing returns
            base_confidence = self.success_rate
            volume_bonus = min(10, self.match_count * 0.5)  # Max 10% bonus
            self.confidence_score = min(100.0, base_confidence + volume_bonus)

    def should_promote(self, threshold: int = 5) -> bool:
        """
        Check if pattern should be promoted.

        Args:
            threshold: Minimum confirmation count for promotion

        Returns:
            True if pattern should be promoted
        """
        return (
            self.confirmation_count >= threshold
            and self.success_rate >= 90.0
            and not self.is_promoted
        )

    def should_demote(self) -> bool:
        """
        Check if pattern should be demoted.

        Returns:
            True if pattern should be demoted
        """
        # Demote if success rate drops below 70%
        return self.success_rate < 70.0 and self.is_promoted
