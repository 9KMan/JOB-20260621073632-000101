// models/delivery_note.py
"""DeliveryNote and DeliveryNoteLine SQLAlchemy models."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
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

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKey

if TYPE_CHECKING:
    from models.invoice import Invoice, InvoiceLine
    from models.purchase_order import PurchaseOrder, PurchaseOrderLine


class DeliveryNote(Base, UUIDPrimaryKey, TimestampMixin, SoftDeleteMixin):
    """Delivery Note header model.

    Represents a delivery note accompanying goods shipped by a supplier.
    """

    __tablename__ = "delivery_notes"
    __table_args__ = (
        Index("ix_dn_supplier_number", "supplier_number"),
        Index("ix_dn_dn_number", "dn_number"),
        Index("ix_dn_status", "status"),
        Index("ix_dn_delivery_date", "delivery_date"),
        UniqueConstraint("dn_number", "supplier_number", name="uq_dn_number_supplier"),
    )

    # Header Information
    dn_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    supplier_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    supplier_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Delivery Information
    delivery_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    shipped_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    # Financial Information
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
        index=True,
    )

    # ERP Reference
    erp_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    erp_sync_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
    )

    # Related PO
    purchase_order_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Carrier Information
    carrier_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    tracking_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
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
    purchase_orders: Mapped[list["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        secondary="po_delivery_notes",
        back_populates="delivery_notes",
        lazy="selectin",
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        secondary="invoice_delivery_notes",
        back_populates="delivery_notes",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number} ({self.status})>"


class DeliveryNoteLine(Base, UUIDPrimaryKey, TimestampMixin):
    """Delivery Note line item model.

    Represents individual line items on a delivery note.
    """

    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_dn_lines_dn_id", "delivery_note_id"),
        Index("ix_dn_lines_line_number", "line_number"),
        Index("ix_dn_lines_sku", "sku"),
    )

    # Parent Delivery Note
    delivery_note_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Line Information
    line_number: Mapped[int] = mapped_column(
        nullable=False,
        index=True,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    # Product Information
    sku: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    product_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    barcode: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    # Quantity and Pricing
    quantity_delivered: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="EA",
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=True,
    )
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    # Related PO Line
    purchase_order_line_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Matching Status
    match_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
    )

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )
    purchase_order_line: Mapped[Optional["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates=None,
    )
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="delivery_note_line",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number}: {self.description[:30]}>"
