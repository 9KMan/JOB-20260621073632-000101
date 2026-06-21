# models/delivery_note.py
"""DeliveryNote and DeliveryNoteLine SQLAlchemy models."""

import uuid
from decimal import Decimal

from sqlalchemy import (
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin
from models.enums import DeliveryNoteStatus


class DeliveryNote(Base, TimestampMixin):
    """Delivery note header model.

    Represents a delivery note received from a vendor or generated
    from goods receipt. Can be linked to PO and invoice.
    """

    __tablename__ = "delivery_notes"

    # Document identification
    dn_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    vendor_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Reference to PO
    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Status
    status: Mapped[DeliveryNoteStatus] = mapped_column(
        default=DeliveryNoteStatus.RECEIVED,
        nullable=False,
        index=True,
    )

    # Dates
    delivery_date: Mapped[Date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    received_date: Mapped[Date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    purchase_order: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder",
        back_populates="delivery_notes",
    )

    __table_args__ = (
        Index("ix_delivery_notes_vendor_id", "vendor_id"),
        Index("ix_delivery_notes_po_id", "purchase_order_id"),
        Index("ix_delivery_notes_delivery_date", "delivery_date"),
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number}>"

    @property
    def total_quantity(self) -> Decimal:
        """Calculate total delivered quantity."""
        return sum(line.quantity for line in self.lines)


class DeliveryNoteLine(Base, TimestampMixin):
    """Delivery note line item model.

    Represents individual line items on a delivery note.
    """

    __tablename__ = "delivery_note_lines"

    delivery_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Line identification
    line_number: Mapped[int] = mapped_column(
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    # Product/supplier references
    product_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    supplier_part_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Quantities
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        default="EA",
        nullable=False,
    )

    # Reference to PO line
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )
    po_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        back_populates="delivery_lines",
    )
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="delivery_line",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_dn_lines_dn_id", "delivery_note_id"),
        Index("ix_dn_lines_po_line_id", "po_line_id"),
        Index("ix_dn_lines_product_code", "product_code"),
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number}: {self.description[:30]}>"

    @property
    def total_invoiced_quantity(self) -> Decimal:
        """Calculate total invoiced quantity against this delivery."""
        return sum(il.matched_quantity for il in self.invoice_lines)

    @property
    def remaining_to_invoice(self) -> Decimal:
        """Calculate remaining quantity that can be invoiced."""
        return max(Decimal("0.0000"), self.quantity - self.total_invoiced_quantity)
