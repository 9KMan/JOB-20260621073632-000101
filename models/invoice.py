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
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import InvoiceStatus, LineStatus, MatchingStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef


class Invoice(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Invoice model representing a supplier invoice."""

    __tablename__ = "invoices"

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
    supplier_tax_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Supplier tax identification number",
    )

    # Invoice Details
    invoice_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Invoice number from supplier",
    )
    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Date on the invoice",
    )
    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Payment due date",
    )
    posting_date: Mapped[date] = mapped_column(
        Date,
        default=lambda: date.today(),
        nullable=False,
        doc="Date posted to the system",
    )

    # Financial
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
        doc="Currency code (ISO 4217)",
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
        doc="Subtotal before tax",
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
        doc="Tax amount",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
        doc="Total invoice amount",
    )

    # Status and Matching
    status: Mapped[InvoiceStatus] = mapped_column(
        String(20),
        default=InvoiceStatus.PENDING,
        nullable=False,
        index=True,
        doc="Invoice status",
    )
    matching_status: Mapped[MatchingStatus] = mapped_column(
        String(20),
        default=MatchingStatus.PENDING,
        nullable=False,
        doc="Matching process status",
    )
    matching_score: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        doc="Matching score percentage (0-100)",
    )
    matched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when invoice was matched",
    )

    # Reference Fields
    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Reference to linked Purchase Order",
    )
    delivery_note_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Reference to linked Delivery Note",
    )

    # Additional Information
    payment_terms: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Payment terms description",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Additional notes",
    )
    is_credit_memo: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether this is a credit memo",
    )
    original_invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
        doc="Reference to original invoice for credit memos",
    )

    # Relationships
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_invoices_supplier_date", "supplier_id", "invoice_date"),
        Index("ix_invoices_status_matching", "status", "matching_status"),
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} - {self.supplier_name}>"


class InvoiceLine(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Invoice line item model."""

    __tablename__ = "invoice_lines"

    # Parent Reference
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Parent invoice ID",
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
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Invoiced quantity",
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        default="EA",
        nullable=False,
        doc="Unit of measure",
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Unit price",
    )
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        doc="Total line amount",
    )
    tax_code: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        doc="Tax code",
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
        doc="Tax rate percentage",
    )

    # Matching
    status: Mapped[LineStatus] = mapped_column(
        String(20),
        default=LineStatus.OPEN,
        nullable=False,
        doc="Line matching status",
    )
    matched_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        doc="Reference to matched PO or DN line",
    )
    matched_line_type: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        doc="Type of matched line (PO_LINE or DN_LINE)",
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
    )
    balance_ledger_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="invoice_line",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_invoice_lines_invoice_number", "invoice_id", "line_number"),
        Index("ix_invoice_lines_product", "product_code"),
    )

    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number}: {self.description}>"
