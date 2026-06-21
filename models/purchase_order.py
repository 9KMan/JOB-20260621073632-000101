# models/purchase_order.py
"""Purchase Order and POLine SQLAlchemy models.

Purchase orders are the anchor for the 3-way matching process.
They contain line items that are matched against invoices and delivery notes.
"""

import uuid
from datetime import date, datetime
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
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.enums import PurchaseOrderStatus, LineStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.delivery_note import DeliveryNoteLine
    from models.invoice import Invoice, InvoiceLine


class POLine(Base):
    """Purchase Order line item model.

    Represents a single line item on a purchase order.
    """

    __tablename__ = "po_lines"
    __table_args__ = (
        UniqueConstraint("po_id", "line_number", name="uq_po_line_number"),
        Index("ix_po_lines_po_id", "po_id"),
        Index("ix_po_lines_product_code", "product_code"),
        {"schema": None},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    product_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    delivered_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    invoiced_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=True)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=True)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=True)
    status: Mapped[LineStatus] = mapped_column(
        String(30),
        default=LineStatus.PENDING,
        nullable=False,
    )
    required_delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    po: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="po_line",
    )
    delivery_note_lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="po_line",
    )
    balance_ledger_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="po_line",
    )

    def __repr__(self) -> str:
        return f"<POLine {self.line_number}: {self.description}>"


class PurchaseOrder(Base):
    """Purchase Order model.

    Represents a purchase order sent to a vendor.
    Acts as the anchor for 3-way matching with invoices and delivery notes.
    """

    __tablename__ = "purchase_orders"
    __table_args__ = (
        UniqueConstraint("po_number", "vendor_id", name="uq_po_vendor"),
        Index("ix_pos_po_number", "po_number"),
        Index("ix_pos_vendor_id", "vendor_id"),
        Index("ix_pos_vendor_code", "vendor_code"),
        Index("ix_pos_status", "status"),
        Index("ix_pos_order_date", "order_date"),
        Index("ix_pos_required_date", "required_delivery_date"),
        {"schema": None},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    po_number: Mapped[str] = mapped_column(String(100), nullable=False)
    vendor_id: Mapped[str] = mapped_column(String(100), nullable=True)
    vendor_code: Mapped[str] = mapped_column(String(50), nullable=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    vendor_tax_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    required_delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    received_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        String(30),
        default=PurchaseOrderStatus.DRAFT,
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    delivered_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    invoiced_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    approved_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    source_system: Mapped[str] = mapped_column(String(50), nullable=True)
    source_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payment_terms: Mapped[str | None] = mapped_column(String(100), nullable=True)
    shipping_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    lines: Mapped[list["POLine"]] = relationship(
        "POLine",
        back_populates="po",
        cascade="all, delete-orphan",
        order_by="POLine.line_number",
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="po",
    )
    delivery_notes: Mapped[list["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="purchase_order",
    )
    balance_ledger_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="purchase_order",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number}: {self.vendor_name} - {self.total_amount}>"
