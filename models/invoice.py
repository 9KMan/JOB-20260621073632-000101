# models/invoice.py
"""
Invoice and InvoiceLine SQLAlchemy models.

The Invoice is the primary document being processed and matched
against Purchase Orders.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

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
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.enums import InvoiceStatus

if TYPE_CHECKING:
    from models.purchase_order import PurchaseOrder
    from models.delivery_note import DeliveryNote
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef


class Invoice(Base):
    """
    Invoice header record.
    
    Represents a supplier invoice received for processing.
    The invoice is matched against one or more Purchase Orders.
    """

    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("invoice_number", "supplier_id", name="uq_invoice_number_supplier"),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_supplier_id", "supplier_id"),
        Index("ix_invoices_invoice_date", "invoice_date"),
        Index("ix_invoices_created_at", "created_at"),
        {
            "comment": "Invoice header table for AP automation",
        },
    )

    # ─── External Identifiers ─────────────────────────────────────────────────
    invoice_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Supplier's invoice number",
    )
    supplier_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Supplier/vendor identifier",
    )
    supplier_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Supplier name (for reference)",
    )
    supplier_tax_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Supplier tax identification number",
    )

    # ─── Financial ───────────────────────────────────────────────────────────
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="EUR",
        comment="ISO 4217 currency code",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
        comment="Invoice total amount in invoice currency",
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
        comment="Tax amount",
    )
    net_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        comment="Net amount (total - tax)",
    )

    # ─── Dates ───────────────────────────────────────────────────────────────
    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Invoice issue date",
    )
    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Payment due date",
    )
    received_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        server_default=func.current_date(),
        comment="Date invoice was received in system",
    )

    # ─── Matching ────────────────────────────────────────────────────────────
    status: Mapped[InvoiceStatus] = mapped_column(
        InvoiceStatus.db_type(),
        nullable=False,
        default=InvoiceStatus.DRAFT,
        index=True,
        comment="Invoice processing status",
    )
    matched_po_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Primary matched PO (if single PO match)",
    )
    match_score: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Matching confidence score (0-100)",
    )
    match_decision: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        comment="Final matching decision",
    )
    matched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when matching was completed",
    )

    # ─── Notes ───────────────────────────────────────────────────────────────
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Internal notes",
    )
    rejection_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Reason for rejection (if applicable)",
    )

    # ─── Relations ───────────────────────────────────────────────────────────
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    matched_po: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder",
        foreign_keys=[matched_po_id],
        backref="matched_invoices",
        lazy="selectin",
    )
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        foreign_keys="CrossRef.invoice_id",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )
    delivery_notes: Mapped[list["DeliveryNote"]] = relationship(
        "DeliveryNote",
        secondary="invoice_delivery_notes",
        back_populates="invoices",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} ({self.status.value})>"

    @property
    def total_lines_count(self) -> int:
        """Return total number of line items."""
        return len(self.lines)

    @property
    def is_active(self) -> bool:
        """Check if invoice is in an active (non-terminal) state."""
        return self.status in InvoiceStatus.active_statuses()

    def to_summary_dict(self) -> dict[str, Any]:
        """Return a summary dictionary for listings."""
        return {
            "id": str(self.id),
            "invoice_number": self.invoice_number,
            "supplier_id": self.supplier_id,
            "supplier_name": self.supplier_name,
            "invoice_date": self.invoice_date.isoformat() if self.invoice_date else None,
            "total_amount": str(self.total_amount),
            "currency": self.currency,
            "status": self.status.value,
            "match_score": self.match_score,
            "match_decision": self.match_decision,
        }


class InvoiceLine(Base):
    """
    Individual line item on an Invoice.
    
    Each line represents a product/service being billed and will be
    matched against corresponding PO lines.
    """

    __tablename__ = "invoice_lines"
    __table_args__ = (
        UniqueConstraint("invoice_id", "line_number", name="uq_invoice_line_number"),
        Index("ix_invoice_lines_invoice_id", "invoice_id"),
        Index("ix_invoice_lines_po_line_id", "po_line_id"),
        {
            "comment": "Invoice line items for AP automation",
        },
    )

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ─── Line Identification ─────────────────────────────────────────────────
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Line item sequence number on invoice",
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Line item description",
    )

    # ─── Product ──────────────────────────────────────────────────────────────
    product_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Product/SKU code",
    )
    product_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Product name",
    )
    uom: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Unit of measure (e.g., 'EA', 'KG', 'HRS')",
    )

    # ─── Quantities & Prices ──────────────────────────────────────────────────
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
        comment="Invoice quantity",
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
        comment="Unit price",
    )
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
        comment="Line total (quantity * unit_price)",
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0.0000"),
        comment="Tax rate (e.g., 0.1900 for 19%)",
    )

    # ─── Matching ────────────────────────────────────────────────────────────
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("po_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Matched PO line ID",
    )
    matched_quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        comment="Quantity matched to PO line",
    )
    matched_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        comment="Amount matched to PO line",
    )
    match_confidence: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Line-level match confidence (0-100)",
    )

    # ─── Relations ───────────────────────────────────────────────────────────
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="lines")
    po_line: Mapped["POLine | None"] = relationship(
        "POLine",
        foreign_keys=[po_line_id],
        back_populates="matched_invoice_lines",
    )
    delivery_note_lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        secondary="invoice_line_delivery_note_lines",
        back_populates="invoice_lines",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number}: {self.description[:30]}>"

    def to_summary_dict(self) -> dict[str, Any]:
        """Return a summary dictionary."""
        return {
            "id": str(self.id),
            "line_number": self.line_number,
            "description": self.description,
            "product_code": self.product_code,
            "quantity": str(self.quantity),
            "unit_price": str(self.unit_price),
            "line_amount": str(self.line_amount),
            "uom": self.uom,
            "po_line_id": str(self.po_line_id) if self.po_line_id else None,
            "match_confidence": self.match_confidence,
        }


# Association table for Invoice <-> DeliveryNote (many-to-many)
from sqlalchemy import Table, Column

invoice_delivery_notes = Table(
    "invoice_delivery_notes",
    Base.metadata,
    Column("invoice_id", UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), primary_key=True),
    Column("delivery_note_id", UUID(as_uuid=True), ForeignKey("delivery_notes.id", ondelete="CASCADE"), primary_key=True),
)

invoice_line_delivery_note_lines = Table(
    "invoice_line_delivery_note_lines",
    Base.metadata,
    Column("invoice_line_id", UUID(as_uuid=True), ForeignKey("invoice_lines.id", ondelete="CASCADE"), primary_key=True),
    Column("delivery_note_line_id", UUID(as_uuid=True), ForeignKey("delivery_note_lines.id", ondelete="CASCADE"), primary_key=True),
)
