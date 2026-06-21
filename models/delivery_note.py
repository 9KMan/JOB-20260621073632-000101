// models/delivery_note.py
"""Delivery Note and DeliveryNoteLine SQLAlchemy models.

This module defines the database models for delivery notes (goods receipt)
received from ERP/OCR systems, used for three-way matching.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, UUIDMixin, TimestampMixin
from models.enums import DeliveryNoteStatus


if TYPE_CHECKING:
    from models.invoice import InvoiceLine
    from models.purchase_order import PurchaseOrderLine


class DeliveryNote(Base, UUIDMixin, TimestampMixin):
    """Delivery Note model (Goods Receipt).

    Represents a delivery note confirming goods have been received,
    used for three-way matching with invoices and purchase orders.

    Attributes:
        dn_number: Unique delivery note number.
        supplier_id: External supplier identifier.
        supplier_name: Supplier name for reference.
        po_reference: Reference to related PO number.
        delivery_date: Date goods were delivered.
        received_by: Name of person who received goods.
        currency: ISO currency code.
        total_amount: Total delivery amount.
        status: Current delivery note status.
        notes: Additional notes.
        metadata: JSON field for additional data.
    """

    __tablename__ = "delivery_notes"
    __table_args__ = (
        Index("ix_delivery_notes_supplier_id", "supplier_id"),
        Index("ix_delivery_notes_dn_number", "dn_number"),
        Index("ix_delivery_notes_po_reference", "po_reference"),
        Index("ix_delivery_notes_status", "status"),
        Index("ix_delivery_notes_delivery_date", "delivery_date"),
        {"comment": "Delivery notes for three-way matching"},
    )

    # DN identification
    dn_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        doc="Unique delivery note number",
    )
    supplier_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="External supplier identifier",
    )
    supplier_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Supplier name for reference",
    )
    po_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Reference to related PO number",
    )

    # Dates
    delivery_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Date goods were delivered",
    )
    received_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Date goods were received in system",
    )

    # Financial
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        doc="ISO currency code",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Total delivery amount",
    )

    # Status
    status: Mapped[DeliveryNoteStatus] = mapped_column(
        String(50),
        nullable=False,
        default=DeliveryNoteStatus.CONFIRMED,
        doc="Current delivery note status",
    )

    # Additional fields
    received_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Name of person who received goods",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Additional notes",
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        type_=Text,
        nullable=True,
        doc="JSON field for additional data",
    )

    # Relationships
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
        doc="Line items on this delivery note",
    )

    def __repr__(self) -> str:
        """String representation of the delivery note."""
        return (
            f"<DeliveryNote(id={self.id}, "
            f"dn_number={self.dn_number}, "
            f"supplier_id={self.supplier_id}, "
            f"status={self.status.value})>"
        )


class DeliveryNoteLine(Base, UUIDMixin, TimestampMixin):
    """Delivery Note Line item model.

    Represents individual line items on a delivery note that
    will be matched against purchase order lines and invoice lines.

    Attributes:
        line_number: Line item sequence number.
        description: Line item description.
        product_code: Product/SKU code.
        quantity: Delivered quantity.
        unit_of_measure: Unit of measure.
        unit_price: Price per unit.
        line_total: Total line amount.
        po_line_id: Reference to matched PO line.
        invoiced_quantity: Total quantity invoiced.
    """

    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_delivery_note_lines_dn_id", "delivery_note_id"),
        Index("ix_delivery_note_lines_po_line_id", "po_line_id"),
        Index("ix_delivery_note_lines_product_code", "product_code"),
        {"comment": "Line items on delivery notes"},
    )

    # Foreign key
    delivery_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "delivery_notes.id",
            ondelete="CASCADE",
            match="FULL",
        ),
        nullable=False,
        doc="Reference to parent delivery note",
    )

    # Line identification
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Line item sequence number",
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Line item description",
    )
    product_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Product/SKU code",
    )

    # Quantities and pricing
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Delivered quantity",
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="EA",
        doc="Unit of measure",
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Price per unit",
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        doc="Total line amount",
    )

    # Matching references
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "purchase_order_lines.id",
            ondelete="SET NULL",
            match="FULL",
        ),
        nullable=True,
        doc="Reference to matched PO line",
    )

    # Tracking
    invoiced_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
        doc="Total quantity invoiced against this delivery",
    )

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
        lazy="selectin",
        doc="Parent delivery note",
    )
    po_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        back_populates="delivery_lines",
        foreign_keys=[po_line_id],
        lazy="selectin",
        doc="Matched PO line",
    )
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="delivery_line",
        foreign_keys="InvoiceLine.delivery_line_id",
        lazy="selectin",
        doc="Invoice lines matched to this delivery line",
    )

    @property
    def remaining_quantity(self) -> Decimal:
        """Calculate remaining quantity not yet invoiced."""
        return self.quantity - self.invoiced_quantity

    def __repr__(self) -> str:
        """String representation of the delivery note line."""
        return (
            f"<DeliveryNoteLine(id={self.id}, "
            f"line_number={self.line_number}, "
            f"product_code={self.product_code}, "
            f"quantity={self.quantity})>"
        )
