# models/delivery_note.py
"""DeliveryNote and DeliveryNoteLine SQLAlchemy models."""

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import DeliveryNoteStatus, LineStatus

if TYPE_CHECKING:
    from models.invoice import Invoice
    from models.purchase_order import PurchaseOrderLine
    from models.balance_ledger import BalanceLedger


class DeliveryNote(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Delivery Note / Goods Receipt model."""

    __tablename__ = "delivery_notes"

    # Supplier Information
    supplier_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Supplier/Vendor ID",
    )
    supplier_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Supplier/Vendor name",
    )

    # DN Details
    dn_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        doc="Delivery Note number",
    )
    dn_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Delivery Note date",
    )
    receipt_date: Mapped[date] = mapped_column(
        Date,
        nullable=True,
        doc="Date goods were received",
    )

    # Reference
    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Reference to Purchase Order",
    )

    # Financial
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
        doc="Currency code (ISO 4217)",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
        doc="Total DN amount",
    )

    # Status
    status: Mapped[DeliveryNoteStatus] = mapped_column(
        String(20),
        default=DeliveryNoteStatus.ISSUED,
        nullable=False,
        index=True,
        doc="DN status",
    )

    # Additional Information
    delivery_address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Delivery address",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Additional notes",
    )

    # Relationships
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="delivery_note",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_delivery_notes_supplier", "supplier_id"),
        Index("ix_delivery_notes_po", "purchase_order_id"),
        Index("ix_delivery_notes_status_date", "status", "dn_date"),
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number} - {self.supplier_name}>"


class DeliveryNoteLine(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Delivery Note Line Item model."""

    __tablename__ = "delivery_note_lines"

    # Parent Reference
    delivery_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Parent DN ID",
    )

    # Reference to PO Line
    purchase_order_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Reference to PO Line",
    )

    # Line Details
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Line item number",
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Line item description",
    )
    product_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        doc="Product/Item code",
    )

    # Quantities
    quantity_delivered: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Delivered quantity",
    )
    quantity_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0.00"),
        nullable=False,
        doc="Invoiced quantity",
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        default="EA",
        nullable=False,
        doc="Unit of measure",
    )

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        doc="Unit price (may be from PO)",
    )
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        doc="Total line amount",
    )

    # Status
    status: Mapped[LineStatus] = mapped_column(
        String(20),
        default=LineStatus.OPEN,
        nullable=False,
        doc="Line status",
    )

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )
    purchase_order_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        back_populates="delivery_note_lines",
    )
    balance_ledger_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="delivery_note_line",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_delivery_note_lines_dn_number", "delivery_note_id", "line_number"),
        Index("ix_delivery_note_lines_po_line", "purchase_order_line_id"),
        Index("ix_delivery_note_lines_product", "product_code"),
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number}: {self.description}>"

    @property
    def quantity_remaining(self) -> Decimal:
        """Calculate remaining quantity to invoice."""
        return self.quantity_delivered - self.quantity_invoiced
