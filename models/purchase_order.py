# models/purchase_order.py
"""Purchase order and purchase order line models."""

import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import Currency, PurchaseOrderStatus, LineType


class PurchaseOrder(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Purchase order header model."""

    __tablename__ = "purchase_orders"

    # Vendor Information
    vendor_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    vendor_tax_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # PO Details
    po_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    po_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    
    # Financial
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, index=True)
    
    # Status
    status: Mapped[str] = mapped_column(
        String(30),
        default=PurchaseOrderStatus.OPEN.value,
        nullable=False,
        index=True
    )
    
    # Delivery
    expected_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    delivery_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # ERP Reference
    erp_po_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

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
        back_populates="purchase_order",
        lazy="selectin",
    )
    balance_ledger: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_purchase_orders_vendor_status", "vendor_code", "status"),
    )


class PurchaseOrderLine(Base, UUIDMixin, TimestampMixin):
    """Purchase order line item model."""

    __tablename__ = "purchase_order_lines"

    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Line Details
    line_number: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    line_type: Mapped[str] = mapped_column(String(20), default=LineType.STANDARD.value, nullable=False)
    
    # Quantities
    quantity_ordered: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    quantity_unit: Mapped[str] = mapped_column(String(20), default="EA", nullable=False)
    quantity_received: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False, default=Decimal("0"))
    quantity_invoiced: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False, default=Decimal("0"))
    
    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"), nullable=False)
    
    # Product Reference
    product_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    product_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # ERP Reference
    erp_line_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship("PurchaseOrder", back_populates="lines")
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="purchase_order_line",
        lazy="selectin",
    )
    delivery_note_lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
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
        """Calculate remaining quantity to invoice."""
        return self.quantity_ordered - self.quantity_invoiced

    @property
    def is_fully_invoiced(self) -> bool:
        """Check if line is fully invoiced."""
        return self.quantity_invoiced >= self.quantity_ordered

    @property
    def is_fully_received(self) -> bool:
        """Check if line is fully received."""
        return self.quantity_received >= self.quantity_ordered


from models.invoice import Invoice, InvoiceLine
from models.delivery_note import DeliveryNote, DeliveryNoteLine
from models.balance_ledger import BalanceLedger
from models.cross_ref import CrossRef
