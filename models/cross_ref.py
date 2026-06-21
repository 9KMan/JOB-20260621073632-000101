# models/cross_ref.py
"""CrossRef SQLAlchemy model for learning loop / matching history."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import ExceptionType, MatchingDecision

if TYPE_CHECKING:
    from models.invoice import InvoiceLine
    from models.purchase_order import POLine
    from models.delivery_note import DeliveryNoteLine


class CrossRef(UUIDMixin, TimestampMixin, Base):
    """Cross Reference model for tracking match history and learning.

    This table stores all matching decisions (automatic and manual) to
    enable the learning loop that improves future matching accuracy.
    """

    __tablename__ = "cross_ref"
    __table_args__ = (
        Index("ix_cross_ref_invoice_line_id", "invoice_line_id"),
        Index("ix_cross_ref_po_line_id", "po_line_id"),
        Index("ix_cross_ref_delivery_line_id", "delivery_line_id"),
        Index("ix_cross_ref_decision", "decision"),
        Index("ix_cross_ref_match_date", "match_date"),
        Index("ix_cross_ref_composite", "vendor_number", "item_number"),
    )

    invoice_line_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("invoice_lines.id", ondelete="CASCADE"),
        nullable=True,
    )
    po_line_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("po_lines.id", ondelete="CASCADE"),
        nullable=True,
    )
    delivery_line_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("delivery_note_lines.id", ondelete="CASCADE"),
        nullable=True,
    )

    vendor_number: Mapped[str] = mapped_column(String(50), nullable=False)
    item_number: Mapped[str] = mapped_column(String(50), nullable=False)
    match_date: Mapped[date] = mapped_column(Date, nullable=False)
    decision: Mapped[MatchingDecision] = mapped_column(String(30), nullable=False)
    match_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    price_match_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    qty_match_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    tolerance_price: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    tolerance_qty: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    invoice_quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4), nullable=True
    )
    po_quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4), nullable=True
    )
    delivery_quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4), nullable=True
    )
    invoice_unit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4), nullable=True
    )
    po_unit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4), nullable=True
    )

    exception_type: Mapped[ExceptionType | None] = mapped_column(
        String(30), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    confirmed: Mapped[bool] = mapped_column(default=False, nullable=False)
    confirmed_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    confirmed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    promotion_count: Mapped[int] = mapped_column(default=0, nullable=False)
    last_promoted_at: Mapped[date | None] = mapped_column(Date, nullable=True)

    invoice_line: Mapped["InvoiceLine | None"] = relationship(
        "InvoiceLine", back_populates="cross_refs"
    )
    po_line: Mapped["POLine | None"] = relationship(
        "POLine", back_populates="cross_refs"
    )
    delivery_note_line: Mapped["DeliveryNoteLine | None"] = relationship(
        "DeliveryNoteLine", back_populates="cross_refs"
    )

    def __repr__(self) -> str:
        return f"<CrossRef {self.vendor_number}/{self.item_number}: {self.decision}>"

    @property
    def is_confirmed(self) -> bool:
        """Check if this cross-reference has been confirmed."""
        return self.confirmed

    @property
    def is_promotable(self) -> bool:
        """Check if this cross-reference can be promoted to global rules."""
        return self.confirmed and self.promotion_count >= 3
