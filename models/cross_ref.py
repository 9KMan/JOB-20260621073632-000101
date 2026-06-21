# models/cross_ref.py
"""CrossRef SQLAlchemy model for learning loop / cross-reference table."""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

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
from models.enums import ConfidenceLevel, MatchType

if TYPE_CHECKING:
    pass


class CrossRef(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Cross-reference learning table for confirmed matches.

    This table stores historical matches that have been confirmed by users,
    enabling the system to learn and improve future matching decisions.
    """

    __tablename__ = "cross_refs"

    # Invoice Reference
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=False)
    invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    # PO Reference
    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    po_number: Mapped[str] = mapped_column(String(100), nullable=False)
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    # Delivery Note Reference (optional)
    dn_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    dn_number: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Match Details
    match_type: Mapped[MatchType] = mapped_column(
        MatchType,
        default=MatchType.PO_MATCH,
        nullable=False,
    )
    match_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    price_match: Mapped[bool] = mapped_column(Boolean, default=True)
    qty_match: Mapped[bool] = mapped_column(Boolean, default=True)

    # Matched Values
    invoice_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    invoice_unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    po_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    po_unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)

    # Learning Data
    confidence_level: Mapped[ConfidenceLevel] = mapped_column(
        ConfidenceLevel,
        default=ConfidenceLevel.UNVERIFIED,
        nullable=False,
    )
    confirmation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rejection_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Vendor/SKU Association
    vendor_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    description_pattern: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_promoted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    promoted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_crossref_vendor_sku", "vendor_id", "sku"),
        Index("ix_crossref_confidence", "confidence_level", "is_active"),
        Index("ix_crossref_invoice_po", "invoice_id", "po_id"),
    )

    def __repr__(self) -> str:
        return f"<CrossRef {self.invoice_number} -> {self.po_number} ({self.confidence_level.value})>"

    def confirm_match(self) -> None:
        """Confirm this match and update confidence."""
        self.confirmation_count += 1
        self.last_confirmed_at = datetime.now(timezone.utc)
        self._update_confidence()

    def reject_match(self) -> None:
        """Reject this match and update confidence."""
        self.rejection_count += 1
        self.last_rejected_at = datetime.now(timezone.utc)
        self._update_confidence()

    def _update_confidence(self) -> None:
        """Update confidence level based on confirmation/rejection counts."""
        total = self.confirmation_count + self.rejection_count
        if total == 0:
            self.confidence_level = ConfidenceLevel.UNVERIFIED
        elif self.confirmation_count / total >= 0.9 and self.confirmation_count >= 10:
            self.confidence_level = ConfidenceLevel.GOLD
        elif self.confirmation_count / total >= 0.7 and self.confirmation_count >= 5:
            self.confidence_level = ConfidenceLevel.SILVER
        elif self.confirmation_count / total >= 0.5:
            self.confidence_level = ConfidenceLevel.BRONZE
        else:
            self.confidence_level = ConfidenceLevel.UNVERIFIED

    def promote(self) -> None:
        """Promote this cross-reference to automatic matching."""
        if self.confidence_level in (ConfidenceLevel.GOLD, ConfidenceLevel.SILVER):
            self.is_promoted = True
            self.promoted_at = datetime.now(timezone.utc)
