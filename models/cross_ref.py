# models/cross_ref.py
"""CrossRef SQLAlchemy model for learning loop and cross-reference matching."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from models.delivery_note import DeliveryNote
    from models.invoice import Invoice
    from models.purchase_order import PurchaseOrder


class CrossRef(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Cross-reference table for learning loop and confirmed matches."""

    __tablename__ = "cross_ref"
    __table_args__ = (
        Index("ix_cross_ref_invoice_id", "invoice_id"),
        Index("ix_cross_ref_po_id", "purchase_order_id"),
        Index("ix_cross_ref_dn_id", "delivery_note_id"),
        Index("ix_cross_ref_vendor_number", "vendor_number"),
        Index("ix_cross_ref_match_signature", "match_signature"),
        {"schema": "public"},
    )

    invoice_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("public.invoices.id", ondelete="CASCADE"),
        nullable=True,
    )
    purchase_order_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("public.purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
    )
    delivery_note_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("public.delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
    )
    vendor_number: Mapped[str] = mapped_column(String(50), nullable=False)
    match_signature: Mapped[str] = mapped_column(String(255), nullable=False)
    confidence_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("1.0000"),
        nullable=False,
    )
    match_count: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    is_promoted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    is_confirmed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    confirmed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    metadata_json: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    invoice: Mapped["Invoice | None"] = relationship(
        "Invoice",
        back_populates="cross_refs",
    )
    purchase_order: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder",
        back_populates="cross_refs",
    )
    delivery_note: Mapped["DeliveryNote | None"] = relationship(
        "DeliveryNote",
        back_populates="cross_refs",
    )
