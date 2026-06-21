// models/purchase_order.py
"""PurchaseOrder and PurchaseOrderLine SQLAlchemy models."""

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
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef
    from models.delivery_note import DeliveryNote
    from models.invoice import Invoice


class PurchaseOrder(Base, UUIDPrimaryKey, TimestampMixin, SoftDeleteMixin):
    """Purchase Order header model.

    Represents a purchase order sent to a supplier.
    """

    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_pos_supplier_number", "supplier_number"),
        Index("ix_pos_po_number", "po_number"),
        Index("ix_pos_status", "status"),
        Index("ix_pos_order_date", "order_date"),
        UniqueConstraint("po_number", "supplier_number", name="uq_po_number_supplier"),
    )

    # Header Information
    po_number: Mapped[str] = mapped_column(
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
    supplier_address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    supplier_tax_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    # Financial Information
    order_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    expected_delivery_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
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
        index=True,
    )
    erp_sync_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="synced",
    )

    # Payment Terms
    payment_terms: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    # Delivery Address
    delivery_address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="purchase_order",
        lazy="selectin",
    )
    delivery_notes: Mapped[list["DeliveryNote"]] = relationship(
        "DeliveryNote",
        secondary="po_delivery_notes",
        back_populates="purchase_orders",
        lazy="selectin",
    )
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="purchase_order",
        lazy="selectin",
    )

    @property
    def open_amount(self) -> Decimal:
        """Calculate the remaining open amount for this PO."""
        from models.balance_ledger import BalanceLedger

        invoiced = sum(
            line.invoiced_amount for line in self.lines
        )
        return self.total_amount - invoiced

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number} ({self.status})>"


class PurchaseOrderLine(Base, UUIDPrimaryKey, TimestampMixin):
    """Purchase Order line item model.

    Represents individual line items on a purchase order.
    """

    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        Index("ix_po_lines_po_id", "purchase_order_id"),
        Index("ix_po_lines_line_number", "line_number"),
        Index("ix_po_lines_sku", "sku"),
    )

    # Parent Purchase Order
    purchase_order_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
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
    manufacturer_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    barcode: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    # Quantity and Pricing
    quantity_ordered: Mapped[Decimal] = mapped_column(
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
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="EA",
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Delivery Information
    delivery_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="purchase_order_line",
        lazy="selectin",
    )
    balance_ledger: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="purchase_order_line",
        cascade="all, delete-orphan",
    )

    @property
    def quantity_remaining(self) -> Decimal:
        """Calculate remaining quantity to be invoiced."""
        return self.quantity_ordered - self.quantity_invoiced

    @property
    def amount_remaining(self) -> Decimal:
        """Calculate remaining amount to be invoiced."""
        return self.line_amount - (self.quantity_invoiced * self.unit_price)

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number}: {self.description[:30]}>"


# Association table for PO-delivery note many-to-many relationship
from sqlalchemy import Table, Column
from sqlalchemy import func

po_delivery_notes = Table(
    "po_delivery_notes",
    Base.metadata,
    Column(
        "purchase_order_id",
        UUID(as_uuid=False),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "delivery_note_id",
        UUID(as_uuid=False),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "created_at",
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    ),
)
