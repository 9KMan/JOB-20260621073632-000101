// models/invoice.py
"""Invoice and InvoiceLine SQLAlchemy models.

Represents vendor invoices in the AP automation system.
"""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
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

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import DocumentStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger


class Invoice(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Invoice header model.

    Represents a vendor invoice with metadata and status.
    """

    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_vendor_code", "vendor_code"),
        Index("ix_invoices_invoice_number_vendor", "invoice_number", "vendor_code"),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_invoice_date", "invoice_date"),
        UniqueConstraint("invoice_number", "vendor_code", name="uq_invoice_number_vendor"),
        {"schema": None},
    )

    # External references
    vendor_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=False)
    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    purchase_order_number: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Dates
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    received_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)

    # Financial
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0.00")
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0.00")
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")

    # Matching
    status: Mapped[DocumentStatus] = mapped_column(
        DocumentStatus.db_type(),
        nullable=False,
        default=DocumentStatus.PENDING,
        index=True,
    )
    match_decision: Mapped[str | None] = mapped_column(String(50), nullable=True)
    match_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    match_decision_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Metadata
    is_credit_memo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    original_invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
    )
    reference_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )
    purchase_order: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder",
        back_populates="invoices",
    )
    original_invoice: Mapped["Invoice | None"] = relationship(
        "Invoice",
        remote_side="Invoice.id",
        back_populates="credit_memos",
    )
    credit_memos: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="original_invoice",
    )
    balance_ledger: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="invoice",
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} from {self.vendor_code}>"


class InvoiceLine(Base, UUIDMixin, TimestampMixin):
    """Invoice line item model.

    Represents individual line items on an invoice.
    """

    __tablename__ = "invoice_lines"
    __table_args__ = (
        Index("ix_invoice_lines_po_line_id", "purchase_order_line_id"),
        {"schema": None},
    )

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )
    line_number: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)

    # Product/SKU
    item_code: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    item_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Quantities
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    quantity_unit: Mapped[str] = mapped_column(String(20), nullable=False, default="EA")

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("0.00"))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))

    # PO Line Reference
    purchase_order_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    delivery_note_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Matching
    match_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    match_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    # Delivery
    delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="lines")
    purchase_order_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        back_populates="invoice_lines",
    )
    delivery_note_line: Mapped["DeliveryNoteLine | None"] = relationship(
        "DeliveryNoteLine",
        back_populates="invoice_lines",
    )

    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number}: {self.description}>"
