# models/cross_ref.py
"""Cross Reference model for the learning loop."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import MatchConfidence, MatchDecision, MatchStatus

if TYPE_CHECKING:
    from models.invoice import Invoice
    from models.purchase_order import PurchaseOrderLine


class CrossRef(Base, UUIDMixin, TimestampMixin):
    """
    Cross Reference table for the learning loop.

    This table tracks confirmed matches between invoices and PO lines,
    enabling the system to learn and improve matching accuracy over time.
    """

    __tablename__ = "cross_ref"
    __table_args__ = (
        Index("ix_xref_invoice_id", "invoice_id"),
        Index("ix_xref_po_line_id", "purchase_order_line_id"),
        Index("ix_xref_vendor_item", "vendor_number", "supplier_item_number"),
        Index("ix_xref_item_number", "item_number"),
        Index("ix_xref_match_score", "match_score"),
    )

    # Reference to Invoice
    invoice_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Reference to PO Line
    purchase_order_line_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Match information at time of creation
    match_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    match_decision: Mapped[MatchDecision] = mapped_column(
        Enum(MatchDecision),
        nullable=False,
    )
    match_confidence: Mapped[MatchConfidence] = mapped_column(
        Enum(MatchConfidence),
        nullable=False,
    )
    match_status: Mapped[MatchStatus] = mapped_column(
        Enum(MatchStatus),
        default=MatchStatus.COMPLETED,
        nullable=False,
    )

    # Match criteria details
    price_match_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    quantity_match_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    date_match_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    item_match_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    # Vendor item mapping (learned from confirmed matches)
    vendor_number: Mapped[str] = mapped_column(String(50), nullable=False)
    supplier_item_number: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    our_item_number: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    item_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Standard price learned from confirmed matches
    standard_price: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    standard_quantity: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)

    # Usage tracking for learning algorithm
    times_matched: Mapped[int] = mapped_column(Integer, default=0)
    times_confirmed: Mapped[int] = mapped_column(Integer, default=0)
    times_rejected: Mapped[int] = mapped_column(Integer, default=0)
    confirmation_rate: Mapped[float] = mapped_column(Numeric(5, 4), default=0.0)
    last_matched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Promoted from manual review (becomes a learned match)
    is_promoted: Mapped[bool] = mapped_column(default=False)
    promoted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(default=True)
    deactivated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deactivation_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="cross_refs",
    )
    purchase_order_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
    )

    def __repr__(self) -> str:
        return f"<CrossRef {self.vendor_number}:{self.supplier_item_number} -> {self.our_item_number}>"

    def update_confirmation(
        self,
        confirmed: bool,
        score_delta: float = 0.0,
    ) -> None:
        """Update confirmation stats when a match is confirmed or rejected."""
        self.last_matched_at = datetime.now(timezone.utc)

        if confirmed:
            self.times_confirmed += 1
            self.match_confidence = MatchConfidence.HIGH
        else:
            self.times_rejected += 1

        self.times_matched += 1

        # Update confirmation rate
        if self.times_matched > 0:
            self.confirmation_rate = self.times_confirmed / self.times_matched

        # Update match score with delta
        if score_delta != 0.0:
            self.match_score = max(0.0, min(100.0, self.match_score + score_delta))

        # Deactivate if rejection rate is too high
        if self.times_matched >= 5 and self.confirmation_rate < 0.3:
            self.deactivate("Low confirmation rate")

    def deactivate(self, reason: str | None = None) -> None:
        """Deactivate this cross-reference entry."""
        self.is_active = False
        self.deactivated_at = datetime.now(timezone.utc)
        self.deactivation_reason = reason

    def promote(self) -> None:
        """Promote this manual match to a learned match."""
        self.is_promoted = True
        self.promoted_at = datetime.now(timezone.utc)
