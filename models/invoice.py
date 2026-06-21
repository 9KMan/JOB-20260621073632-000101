# models/invoice.py
"""Invoice and InvoiceLine SQLAlchemy models."""

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
from models.enums import InvoiceStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.purchase_order import PurchaseOrder, PurchaseOrderLine


class Invoice(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Invoice header model."""

    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("invoice_number", "vendor_id", name="uq_invoice_vendor"),
        Index("ix_invoices_vendor_id", "vendor_id"),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_invoice_date", "invoice_date"),
        {"schema": None},
    )

    # Invoice identification
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=False)
    vendor_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    vendor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Invoice dates
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Financial
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0.00"), nullable=False
    )

    # Status and workflow
    status: Mapped[InvoiceStatus] = mapped_column(
        String(50), default=InvoiceStatus.PENDING, nullable=False, index=True
    )

    # Matching references
    matched_po_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="SET NULL"), nullable=True
    )
    match_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    match_decision: Mapped[str | None] = mapped_column(String(50), nullable=True)
    match_confidence: Mapped[str | None] = mapped_column(String(50), nullable=True)
    match_decision_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Payment info
    paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payment_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Additional info
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(Text, nullable=True)

    # ERP reference
    erp_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    matched_po: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder",
        back_populates="matched_invoices",
        foreign_keys=[matched_po_id],
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} - {self.total_amount}>"


class InvoiceLine(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Invoice line item model."""

    __tablename__ = "invoice_lines"
    __table_args__ = (
        Index("ix_invoice_lines_invoice_id", "invoice_id"),
        Index("ix_invoice_lines_line_number", "line_number"),
        {"schema": None},
    )

    # Parent reference
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Line identification
    line_number: Mapped[str] = mapped_column(String(50), nullable=False)
    line_type: Mapped[str] = mapped_column(String(50), default="ITEM", nullable=False)

    # Product/Service
    product_code: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    product_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Quantities
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=Decimal("0.0000"))
    quantity_received: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), default=Decimal("0.0000")
    )
    quantity_invoiced: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=Decimal("0.0000"))

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=Decimal("0.0000"))
    price: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    line_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))

    # Matching references
    matched_po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    match_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="lines")
    matched_po_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        back_populates="matched_invoice_lines",
        foreign_keys=[matched_po_line_id],
    )
    balance_ledger_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="invoice_line",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number} - {self.product_code}>"
