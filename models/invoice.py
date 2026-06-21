# models/invoice.py
"""Invoice and InvoiceLine SQLAlchemy models."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from models.enums import DocumentStatus, LineStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedgerEntry
    from models.purchase_order import PurchaseOrderLine


class Invoice(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Invoice document model."""

    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_vendor_number", "vendor_number"),
        Index("ix_invoices_invoice_number", "invoice_number", unique=True),
        Index("ix_invoices_invoice_date", "invoice_date"),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_created_at", "created_at"),
        UniqueConstraint("invoice_number", name="uq_invoices_invoice_number"),
    )

    # Document reference fields
    invoice_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Unique invoice number from vendor",
    )
    vendor_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Vendor/supplier identifier",
    )
    vendor_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Vendor name",
    )

    # Invoice dates
    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Invoice issue date",
    )
    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Payment due date",
    )

    # Financial amounts
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Invoice subtotal before tax",
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Tax amount",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Total invoice amount",
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        comment="ISO 4217 currency code",
    )

    # Status and workflow
    status: Mapped[DocumentStatus] = mapped_column(
        default=DocumentStatus.DRAFT,
        nullable=False,
        comment="Invoice processing status",
    )
    is_ocr_processed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Whether OCR has processed this invoice",
    )
    ocr_confidence: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="OCR confidence score 0-100",
    )

    # ERP reference
    erp_invoice_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="External ERP invoice ID",
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Additional notes",
    )

    # Relationships
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Invoice(id={self.id}, number={self.invoice_number}, status={self.status})>"


class InvoiceLine(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Invoice line item model."""

    __tablename__ = "invoice_lines"
    __table_args__ = (
        Index("ix_invoice_lines_invoice_id", "invoice_id"),
        Index("ix_invoice_lines_line_number", "line_number"),
        Index("ix_invoice_lines_status", "status"),
        Index("ix_invoice_lines_po_line_id", "po_line_id"),
    )

    # Foreign key to invoice
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Line reference
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Line item sequence number",
    )

    # Product/service info
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Product SKU",
    )
    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Line item description",
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0"),
        comment="Invoiced quantity",
    )
    unit_of_measure: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Unit of measure",
    )

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
        comment="Unit price",
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Line total amount",
    )

    # Status
    status: Mapped[LineStatus] = mapped_column(
        default=LineStatus.OPEN,
        nullable=False,
        comment="Line matching status",
    )

    # Matched PO line reference
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        comment="Matched PO line ID",
    )
    match_confidence: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Match confidence score 0-100",
    )
    matched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of match",
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
    )
    po_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        foreign_keys=[po_line_id],
        back_populates="matched_invoice_lines",
    )
    balance_entries: Mapped[list["BalanceLedgerEntry"]] = relationship(
        "BalanceLedgerEntry",
        back_populates="invoice_line",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<InvoiceLine(id={self.id}, line_number={self.line_number}, qty={self.quantity})>"
