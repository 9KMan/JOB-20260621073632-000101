// models/cross_ref.py
"""Cross Reference SQLAlchemy model for learning loop.

This module defines the CrossRef database model for storing
match history and learning/promotion logic.
"""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import DecisionType, ExceptionReason, ExceptionStatus, MatchStatus

if TYPE_CHECKING:
    from models.delivery_note import DeliveryNote
    from models.invoice import Invoice
    from models.purchase_order import PurchaseOrder


class CrossRef(Base, UUIDMixin, TimestampMixin):
    """Cross Reference model for match history and learning.

    This table stores all match relationships between invoices,
    purchase orders, and delivery notes. It also tracks the
    learning/promotion logic for improving future matches.

    Attributes:
        invoice_id: Associated invoice
        purchase_order_id: Associated PO (if matched)
        delivery_note_id: Associated DN (if matched)
        match_status: Status of the match
        match_score: Confidence score (0-100)
        decision: Final decision from matching engine
        weight: Learning weight for this match
        confirmed: Whether match has been confirmed
        confirmed_at: When match was confirmed
        confirmed_by: Who confirmed the match
        exceptions: List of exceptions
        match_details: JSON blob with detailed match info
        promotion_level: Learning promotion level
    """

    __tablename__ = "cross_refs"
    __table_args__ = (
        Index("ix_cross_refs_invoice_id", "invoice_id"),
        Index("ix_cross_refs_po_id", "purchase_order_id"),
        Index("ix_cross_refs_dn_id", "delivery_note_id"),
        Index("ix_cross_refs_match_status", "match_status"),
        Index("ix_cross_refs_confirmed", "confirmed"),
        Index("ix_cross_refs_weight", "weight"),
    )

    # Foreign keys
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )
    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
    )
    delivery_note_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Match info
    match_status: Mapped[str] = mapped_column(
        String(30),
        default=MatchStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    match_score: Mapped[int | None] = mapped_column(
        default=None,
        nullable=True,
    )
    decision: Mapped[str | None] = mapped_column(
        String(30),
        default=None,
        nullable=True,
    )

    # Learning
    weight: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("1.00"),
        nullable=False,
    )
    confirmed: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        index=True,
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    confirmed_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Price variance tracking
    price_variance: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4),
        nullable=True,
    )
    quantity_variance: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4),
        nullable=True,
    )

    # Metadata
    match_type: Mapped[str] = mapped_column(
        String(50),
        default="auto",
        nullable=False,
    )
    match_details: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
    )
    promotion_level: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    last_promoted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="cross_refs",
    )
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="cross_refs",
    )
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="cross_refs",
    )

    def __repr__(self) -> str:
        return f"<CrossRef {self.id} - Score: {self.match_score}>"

    def confirm_match(self, user_id: str) -> None:
        """Confirm this match and update learning weights.

        Args:
            user_id: ID of user confirming the match
        """
        self.confirmed = True
        self.confirmed_at = datetime.now(timezone.utc)
        self.confirmed_by = user_id
        self._promote()

    def reject_match(self, user_id: str) -> None:
        """Reject this match and decrease learning weights.

        Args:
            user_id: ID of user rejecting the match
        """
        self.confirmed = False
        self.confirmed_at = datetime.now(timezone.utc)
        self.confirmed_by = user_id
        self._demote()

    def _promote(self) -> None:
        """Increase weight based on successful match confirmation."""
        # Increase weight but cap at 2.0
        self.weight = min(self.weight * Decimal("1.1"), Decimal("2.00"))
        self.promotion_level += 1
        self.last_promoted_at = datetime.now(timezone.utc)

    def _demote(self) -> None:
        """Decrease weight based on rejected match."""
        # Decrease weight but floor at 0.5
        self.weight = max(self.weight * Decimal("0.9"), Decimal("0.50"))
        self.promotion_level = max(self.promotion_level - 1, -3)
