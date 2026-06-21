// models/purchase_order.py
"""PurchaseOrder and PurchaseOrderLine SQLAlchemy models.

Purchase orders are created in the ERP system and imported into
the matching engine for invoice verification.
"""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.enums import PurchaseOrderStatus


class PurchaseOrder(Base):
    """Purchase order header model.

    Represents a PO created in the ERP system.
    """

    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_purchase_orders_po_number", "po_number", unique=True),
        Index("ix_purchase_orders_vendor_code", "vendor_code"),
        Index("ix_purchase_orders_status", "status"),
        Index("ix_purchase_orders_created_at", "created_at"),
        Index("ix_purchase_orders_expected_date", "expected_delivery_date"),
    )

    # External references
    po_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    vendor_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    department_code: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # PO dates
    po_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Financial fields
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")

    # Status
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        PurchaseOrderStatus,
        default=PurchaseOrderStatus.DRAFT,
        nullable=False,
    )

    # ERP reference
    erp_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(),
        nullable=False,
    )

    # Metadata
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_data: Mapped[dict | None] = mapped_column(Text, nullable=True)

    # Relationships
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    matched_invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="matched_po",
        foreign_keys="Invoice.matched_po_id",
    )
    balance_ledger_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number} ({self.status.value})>"


class PurchaseOrderLine(Base):
    """Purchase order line item model.

    Represents individual line items on a PO.
    """

    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        Index("ix_purchase_order_lines_po_id", "po_id"),
        Index("ix_purchase_order_lines_line_number", "line_number"),
        Index("ix_purchase_order_lines_sku", "sku"),
    )

    # Parent reference
    po_id: Mapped[UUID] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Line details
    line_number: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    manufacturer_part: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Quantities and amounts
    ordered_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Delivered quantity tracking
    delivered_quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        nullable=False,
        default=Decimal("0"),
    )
    invoiced_quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        nullable=False,
        default=Decimal("0"),
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder", back_populates="lines"
    )
    matched_invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="matched_po_line",
        foreign_keys="InvoiceLine.matched_po_line_id",
    )
    delivery_note_lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="po_line",
        foreign_keys="DeliveryNoteLine.matched_po_line_id",
    )

    @property
    def remaining_quantity(self) -> Decimal:
        """Calculate remaining quantity to be delivered."""
        return self.ordered_quantity - self.delivered_quantity

    @property
    def remaining_to_invoice(self) -> Decimal:
        """Calculate remaining quantity to be invoiced."""
        return self.delivered_quantity - self.invoiced_quantity

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number}: {self.description[:30]}>"


# Import at bottom to avoid circular imports
from models.invoice import Invoice, InvoiceLine
from models.delivery_note import DeliveryNoteLine
from models.balance_ledger import BalanceLedger
