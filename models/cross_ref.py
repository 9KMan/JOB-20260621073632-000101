# models/cross_ref.py
"""CrossRef SQLAlchemy model for the learning loop / confirmed matches."""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from models.purchase_order import PurchaseOrderLine
    from models.invoice import InvoiceLine


class CrossRef(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Cross-Reference table for the learning loop.

    This table stores confirmed matches between PO lines and invoice lines
    to improve future matching accuracy. When a match is confirmed multiple
    times, it gets promoted to this table and receives a score boost.
    """

    __tablename__ = "cross_ref"
    __table_args__ = (
        Index("ix_cross_ref_vendor_number", "vendor_number"),
        Index("ix_cross_ref_sku", "sku"),
        Index("ix_cross_ref_product_code", "product_code"),
        Index("ix_cross_ref_po_line_id", "po_line_id"),
        Index("ix_cross_ref_invoice_line_id", "invoice_line_id"),
        Index("ix_cross_ref_is_active", "is_active"),
        {
            "schema": None,
        },
    )

    # Product/Service Identifiers
    vendor_number: Mapped[str] = mapped_column(String(50), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    product_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description_pattern: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Matched Entities
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Match Statistics
    confirmation_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    match_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    last_matched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Learned Attributes (from confirmed matches)
    learned_unit_price: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    learned_quantity_ratio: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    learned_uom: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    # Confidence & Boost
    base_confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=50.0,
    )
    current_confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=50.0,
    )
    boost_factor: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    is_promoted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    promoted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Manual Overrides
    is_manual_override: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    overridden_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Relationships
    po_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        lazy="selectin",
    )
    invoice_line: Mapped["InvoiceLine | None"] = relationship(
        "InvoiceLine",
        lazy="selectin",
    )

    def promote(self, confirmed_by: str | None = None) -> None:
        """Promote this cross-ref to confirmed status.

        Args:
            confirmed_by: User who confirmed the match
        """
        self.is_promoted = True
        self.promoted_at = datetime.now(timezone.utc)
        self.is_manual_override = confirmed_by is not None
        self.overridden_by = confirmed_by
        self.confirmation_count += 1
        self.update_confidence()

    def record_match(self) -> None:
        """Record a successful match for this cross-ref."""
        self.match_count += 1
        self.last_matched_at = datetime.now(timezone.utc)
        self.confirmation_count += 1
        self.update_confidence()

    def update_confidence(self) -> None:
        """Update the confidence score based on match history."""
        # Simple confidence algorithm:
        # - Start at base_confidence
        # - Add boost for each confirmation (diminishing returns)
        # - Cap at 100
        import math

        if self.confirmation_count <= 1:
            self.current_confidence = self.base_confidence
        else:
            # Diminishing returns: log(confirmation_count + 1) * boost_factor
            boost = math.log(self.confirmation_count + 1) * self.boost_factor
            self.current_confidence = min(
                100.0,
                self.base_confidence + boost,
            )

    def apply_boost(self, boost_amount: float) -> None:
        """Apply a score boost to this cross-ref.

        Args:
            boost_amount: Amount to add to boost_factor
        """
        self.boost_factor += boost_amount
        self.update_confidence()

    def deactivate(self) -> None:
        """Deactivate this cross-ref."""
        self.is_active = False

    def reactivate(self) -> None:
        """Reactivate this cross-ref."""
        self.is_active = True

    def __repr__(self) -> str:
        return (
            f"<CrossRef(id={self.id}, vendor={self.vendor_number}, "
            f"sku={self.sku}, confidence={self.current_confidence:.1f})>"
        )
