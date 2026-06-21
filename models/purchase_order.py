// models/purchase_order.py
"""PurchaseOrder and PurchaseOrderLine SQLAlchemy models.

Represents purchase orders from the ERP system.
"""

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
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
from models.enums import DocumentStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.invoice import Invoice
    from models.delivery_note import DeliveryNoteLine


class PurchaseOrder(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Purchase Order header model.

    Represents a PO from the ERP system.
    """

    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_purchase_orders_po_number", "po_number"),
        Index("ix_purchase_orders_vendor_code", "vendor_code"),
        Index("ix_purchase_orders_status", "status"),
        Index("ix_purchase_orders_po_date", "po_date"),
        UniqueConstraint("po_number", name="uq_po_number"),
        {"schema": None},
    )

    # PO Identification
    po_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    vendor_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Dates
    po_date: Mapped[date] = mapped_column(Date, nullable=False)
    required_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    promised_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Financial
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0.00")
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")

    # Status
    status: Mapped[DocumentStatus] = mapped_column(
        DocumentStatus.db_type(),
        nullable=False,
        default=DocumentStatus.SUBMITTED,
        index=True,
    )

    # Additional Info
    buyer: Mapped[str | None] = mapped_column(String(100), nullable=True)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ship_to: Mapped[str | None] = mapped_column(String(255), nullable=True)
    terms: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_blanket_po: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="purchase_order",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number}>"


class PurchaseOrderLine(Base, UUIDMixin, TimestampMixin):
    """Purchase Order Line Item model.

    Represents individual line items on a purchase order.
    """

    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        Index("ix_po_lines_po_id", "purchase_order_id"),
        Index("ix_po_lines_item_code", "item_code"),
        {"schema": None},
    )

    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    line_number: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)

    # Product/SKU
    item_code: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    item_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Quantities
    quantity_ordered: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    quantity_received: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0.00")
    )
    quantity_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0.00")
    )
    quantity_unit: Mapped[str] = mapped_column(String(20), nullable=False, default="EA")

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("0.00"))

    # Delivery
    required_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    promised_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Status
    line_status: Mapped[str] = mapped_column(String(50), nullable=False, default="open")

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="purchase_order_line",
    )
    delivery_note_lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="purchase_order_line",
    )
    balance_ledger: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="purchase_order_line",
    )

    @property
    def quantity_pending(self) -> Decimal:
        """Calculate pending quantity (ordered - received)."""
        return self.quantity_ordered - self.quantity_received

    @property
    def quantity_to_invoice(self) -> Decimal:
        """Calculate quantity available for invoicing (received - invoiced)."""
        return self.quantity_received - self.quantity_invoiced

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number}: {self.description}>"
