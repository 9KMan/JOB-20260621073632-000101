# models/delivery_note.py
"""Delivery Note model for AP Automation Core Engine."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from models.enums import DeliveryNoteStatus

if TYPE_CHECKING:
    from models.invoice import InvoiceLine
    from models.purchase_order import PurchaseOrderLine


class DeliveryNoteLine(TimestampMixin, UUIDPrimaryKeyMixin, Base):
    """Individual line item on a Delivery Note."""

    __tablename__ = "delivery_note_lines"

    delivery_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Line identification
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    external_line_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    # Product info
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    unit_of_measure: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Quantities
    quantity_delivered: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    quantity_received: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )
    quantity_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )

    # Link to PO
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )
    po_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        foreign_keys=[po_line_id],
    )
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="matched_dn_line",
        foreign_keys="InvoiceLine.matched_dn_line_id",
    )

    __table_args__ = (
        Index("ix_dn_lines_dn_sku", "delivery_note_id", "sku"),
    )

    @property
    def balance_quantity(self) -> Decimal:
        """Remaining uninvoiced quantity."""
        return self.quantity_delivered - self.quantity_invoiced


class DeliveryNote(TimestampMixin, SoftDeleteMixin, UUIDPrimaryKeyMixin, Base):
    """Delivery Note model representing goods receipts.

    Delivery Notes (DNs) capture what was actually delivered and
    are used as evidence for invoice matching.
    """

    __tablename__ = "delivery_notes"

    # External reference
    external_dn_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    dn_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Supplier info
    supplier_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    supplier_tax_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Related PO
    po_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    po_number: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Dates
    dn_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    received_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Financial info
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Status
    status: Mapped[DeliveryNoteStatus] = mapped_column(
        String(20),
        nullable=False,
        default=DeliveryNoteStatus.DRAFT,
        index=True,
    )

    # Source info
    source_system: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_document_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Warehouse info
    warehouse_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    received_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    quality_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        order_by="DeliveryNoteLine.line_number",
    )

    __table_args__ = (
        Index("ix_dns_supplier_date", "supplier_id", "dn_date"),
        Index("ix_dns_po", "po_id"),
        Index("ix_dns_status_date", "status", "dn_date"),
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number} - {self.total_amount} {self.currency}>"

    @property
    def total_delivered_quantity(self) -> Decimal:
        """Total delivered quantity across all lines."""
        return sum(line.quantity_delivered for line in self.lines)

    @property
    def total_invoiced_quantity(self) -> Decimal:
        """Total invoiced quantity across all lines."""
        return sum(line.quantity_invoiced for line in self.lines)


__all__ = ["DeliveryNote", "DeliveryNoteLine"]
