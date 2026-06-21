# models/cross_ref.py
"""Cross Reference (Learning Loop) SQLAlchemy model."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from models.invoice import Invoice, InvoiceLine
    from models.purchase_order import POLine


class CrossRef(Base, UUIDMixin, TimestampMixin):
    """Cross Reference model for learning/promotion logic.

    Tracks confirmed matches between PO lines and Invoice lines
    to improve future matching accuracy.
    """

    __tablename__ = "cross_ref"

    po_line_id: Mapped[UUID] = mapped_column(
        PG_UUID,
        ForeignKey("po_lines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    invoice_id: Mapped[UUID] = mapped_column(
        PG_UUID,
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    invoice_line_id: Mapped[UUID] = mapped_column(
        PG_UUID,
        ForeignKey("invoice_lines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Matching characteristics
    vendor_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    part_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    description_similarity: Mapped[float] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=0.0,
    )
    quantity_match: Mapped[float] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=0.0,
    )
    price_match: Mapped[float] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=0.0,
    )
    overall_score: Mapped[float] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=0.0,
    )
    # Confirmation data
    confirmed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )
    confirmed_by: Mapped[UUID | None] = mapped_column(
        PG_UUID,
        nullable=True,
    )
    # Learning data
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
    # Promotion status
    promoted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    promotion_score: Mapped[float] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=0.0,
    )
    promotion_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Relationships
    po_line: Mapped["POLine"] = relationship(
        "POLine",
        back_populates="cross_refs",
    )
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="cross_refs",
    )

    __table_args__ = (
        Index("ix_cross_ref_vendor_part", "vendor_id", "part_number"),
        Index("ix_cross_ref_promoted", "promoted", "promotion_level"),
        Index("ix_cross_ref_confirmed", "confirmed", "confirmation_count"),
    )
