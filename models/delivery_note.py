# models/delivery_note.py
"""DeliveryNote and DeliveryNoteLine SQLAlchemy models."""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import DeliveryNoteStatus

if TYPE_CHECKING:
    from models.purchase_order import PurchaseOrderLine


class DeliveryNote(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Delivery Note header model."""

    __tablename__ = "delivery_notes"
    __table_args__ = (
        UniqueConstraint("dn_number", "vendor_id", name="uq_dn_vendor"),
        Index("ix_delivery_notes_vendor_id", "vendor_id"),
        Index("ix_delivery_notes_status", "status"),
        Index("ix_delivery_notes_dn_date", "dn_date"),
        {"schema": None},
    )

    # DN identification
    dn_number: Mapped[str] = mapped_column(String(100), nullable=False)
    vendor_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    vendor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Reference to PO
    po_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    po_number: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # DN dates
    dn_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    actual_delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Status
    status: Mapped[DeliveryNoteStatus] = mapped_column(
        String(50), default=DeliveryNoteStatus.ISSUED, nullable=False, index=True
    )

    # Shipping info
    ship_from: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ship_to: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tracking_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    carrier: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Financial
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    # Additional info
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(Text, nullable=True)

    # ERP reference
    erp_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number}>"


class DeliveryNoteLine(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Delivery Note line item model."""

    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_delivery_note_lines_dn_id", "dn_id"),
        Index("ix_delivery_note_lines_line_number", "line_number"),
        Index("ix_delivery_note_lines_product_code", "product_code"),
        {"schema": None},
    )

    # Parent reference
    dn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Reference to PO line
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Line identification
    line_number: Mapped[str] = mapped_column(String(50), nullable=False)

    # Product/Service
    product_code: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    product_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Quantities
    quantity_shipped: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=Decimal("0.0000"))
    quantity_received: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=Decimal("0.0000"))
    quantity_returned: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=Decimal("0.0000"))

    # Pricing (for reference)
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    line_total: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    # Status flags
    is_received: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_fully_matched: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Matching score
    match_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote", back_populates="lines"
    )
    po_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        back_populates="delivery_note_lines",
        foreign_keys=[po_line_id],
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number} - {self.product_code}>"

    @property
    def net_quantity(self) -> Decimal:
        """Calculate net quantity after returns."""
        return self.quantity_received - self.quantity_returned
