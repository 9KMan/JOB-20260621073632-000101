// models/invoice.py
"""Invoice and InvoiceLine SQLAlchemy models.

This module defines the invoice data model for the AP automation system.
Invoices are the primary entity that gets matched against purchase orders
and delivery notes for automated approval processing.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
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

from models.base import Base
from models.enums import InvoiceStatus, LineStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.purchase_order import POLine


class Invoice(Base):
    """Invoice model representing an accounts payable invoice.
    
    Attributes:
        id: UUID primary key
        invoice_number: Unique invoice number from vendor
        vendor_code: Vendor identifier code
        vendor_name: Vendor name
        vendor_tax_id: Vendor tax identification number
        invoice_date: Date on the invoice
        due_date: Payment due date
        subtotal: Invoice subtotal before tax
        tax_amount: Tax amount
        total_amount: Total invoice amount including tax
        currency: Currency code (ISO 4217)
        status: Current invoice status
        notes: Optional notes/comments
        is_credit_note: Whether this is a credit note
        payment_reference: Payment reference when processed
        approved_by: User who approved the invoice
        approved_at: When invoice was approved
        matched_at: When invoice was matched
        exception_id: Related exception ID if in exception status
        metadata: Additional JSON metadata
        lines: Related invoice lines
        created_at: Record creation timestamp
        updated_at: Record update timestamp
    """

    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_vendor_code", "vendor_code"),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_invoice_date", "invoice_date"),
        Index("ix_invoices_created_at", "created_at"),
        UniqueConstraint("invoice_number", "vendor_code", name="uq_invoice_number_vendor"),
    )

    # Primary identifiers
    invoice_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Unique invoice number",
    )
    vendor_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Vendor code",
    )
    vendor_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Vendor name",
    )
    vendor_tax_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="Vendor tax ID",
    )

    # Dates
    invoice_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="Invoice date",
    )
    due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Payment due date",
    )

    # Financial amounts
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Subtotal before tax",
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Tax amount",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Total amount including tax",
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        doc="Currency code (ISO 4217)",
    )

    # Status and workflow
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus, name="invoice_status"),
        nullable=False,
        default=InvoiceStatus.DRAFT,
        doc="Current invoice status",
    )
    is_credit_note: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether this is a credit note",
    )

    # Processing details
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Internal notes",
    )
    payment_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Payment reference number",
    )
    approved_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="User who approved",
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Approval timestamp",
    )
    matched_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Matching completion timestamp",
    )

    # Exception handling
    exception_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        doc="Related exception ID",
    )

    # Additional data
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        Text,
        nullable=True,
        doc="Additional JSON metadata",
    )

    # Relationships
    lines: Mapped[List["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} vendor={self.vendor_code} status={self.status.value}>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": str(self.id),
            "invoice_number": self.invoice_number,
            "vendor_code": self.vendor_code,
            "vendor_name": self.vendor_name,
            "vendor_tax_id": self.vendor_tax_id,
            "invoice_date": self.invoice_date.isoformat() if self.invoice_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "subtotal": str(self.subtotal),
            "tax_amount": str(self.tax_amount),
            "total_amount": str(self.total_amount),
            "currency": self.currency,
            "status": self.status.value,
            "is_credit_note": self.is_credit_note,
            "notes": self.notes,
            "payment_reference": self.payment_reference,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "matched_at": self.matched_at.isoformat() if self.matched_at else None,
            "exception_id": str(self.exception_id) if self.exception_id else None,
            "lines": [line.to_dict() for line in self.lines],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class InvoiceLine(Base):
    """Invoice line item model.
    
    Represents individual line items on an invoice, each of which
    can be matched to specific PO and delivery note lines.
    
    Attributes:
        id: UUID primary key
        invoice_id: Parent invoice ID
        line_number: Line item number
        description: Line item description
        quantity: Invoice quantity
        unit_of_measure: UOM code
        unit_price: Price per unit
        line_amount: Total line amount (quantity * unit_price)
        currency: Currency code
        po_line_id: Matched PO line ID (optional)
        dn_line_id: Matched delivery note line ID (optional)
        status: Line matching status
        matched_at: When line was matched
        match_score: Match confidence score (0-100)
        match_decision: Match decision outcome
        metadata: Additional JSON metadata
    """

    __tablename__ = "invoice_lines"
    __table_args__ = (
        Index("ix_invoice_lines_invoice_id", "invoice_id"),
        Index("ix_invoice_lines_po_line_id", "po_line_id"),
        Index("ix_invoice_lines_status", "status"),
        Index("ix_invoice_lines_line_number", "line_number"),
    )

    # Parent reference
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        doc="Parent invoice ID",
    )

    # Line identifiers
    line_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Line item number",
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Line item description",
    )
    sku: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Product SKU",
    )
    gtin: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        doc="Global Trade Item Number",
    )

    # Quantities and amounts
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Invoice quantity",
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="EA",
        doc="Unit of measure code",
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
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        doc="Currency code",
    )

    # Matching references
    po_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("po_lines.id", ondelete="SET NULL"),
        nullable=True,
        doc="Matched PO line ID",
    )
    dn_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
        doc="Matched delivery note line ID",
    )

    # Matching status
    status: Mapped[LineStatus] = mapped_column(
        Enum(LineStatus, name="line_status"),
        nullable=False,
        default=LineStatus.PENDING,
        doc="Line matching status",
    )
    matched_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Matching timestamp",
    )
    match_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Match confidence score (0-100)",
    )
    match_decision: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="Match decision outcome",
    )

    # Exception details
    price_variance: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Price variance percentage",
    )
    quantity_variance: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Quantity variance percentage",
    )

    # Additional data
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        Text,
        nullable=True,
        doc="Additional JSON metadata",
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
    )
    po_line: Mapped[Optional["POLine"]] = relationship(
        "POLine",
        foreign_keys=[po_line_id],
    )
    balance_ledger: Mapped[Optional["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="invoice_line",
        uselist=False,
    )

    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number} qty={self.quantity} amt={self.line_amount}>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": str(self.id),
            "invoice_id": str(self.invoice_id),
            "line_number": self.line_number,
            "description": self.description,
            "sku": self.sku,
            "gtin": self.gtin,
            "quantity": str(self.quantity),
            "unit_of_measure": self.unit_of_measure,
            "unit_price": str(self.unit_price),
            "line_amount": str(self.line_amount),
            "currency": self.currency,
            "po_line_id": str(self.po_line_id) if self.po_line_id else None,
            "dn_line_id": str(self.dn_line_id) if self.dn_line_id else None,
            "status": self.status.value if self.status else None,
            "matched_at": self.matched_at.isoformat() if self.matched_at else None,
            "match_score": self.match_score,
            "match_decision": self.match_decision,
            "price_variance": self.price_variance,
            "quantity_variance": self.quantity_variance,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def is_matched(self) -> bool:
        """Check if line is successfully matched."""
        return self.status in LineStatus.matched_statuses()

    @property
    def has_exception(self) -> bool:
        """Check if line has an exception."""
        return self.status == LineStatus.EXCEPTION or self.exception_type is not None

    @property
    def exception_type(self) -> Optional[str]:
        """Get exception type if any."""
        if self.price_variance is not None and abs(self.price_variance) > 0.01:
            return "price_variance"
        if self.quantity_variance is not None and abs(self.quantity_variance) > 0.01:
            return "quantity_variance"
        return None
