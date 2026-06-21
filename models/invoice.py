// models/invoice.py
"""Invoice model definition.

This module defines the Invoice and InvoiceLine SQLAlchemy models
with their relationships and methods.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.enums import InvoiceStatus, LineStatus


class Invoice(Base):
    """Invoice database model.

    Represents an accounts payable invoice received from a vendor.
    """

    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_vendor_number", "vendor_number"),
        Index("ix_invoices_invoice_date", "invoice_date"),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_tenant_status", "tenant_id", "status"),
        {"schema": None},
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # Invoice identification
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=False)
    vendor_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=True)

    # Invoice details
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    received_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Financial amounts
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")

    # Status and workflow
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=InvoiceStatus.RECEIVED.value,
        index=True,
    )

    # Matching reference
    match_decision: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    match_confidence: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    match_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    match_decision_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    matched_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    # Approval workflow
    approved_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    rejected_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    rejected_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Tax and compliance
    tax_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)

    # Additional metadata
    reference_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payment_terms: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Soft delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )
    matched_pos: Mapped[list["InvoicePurchaseOrder"]] = relationship(
        "InvoicePurchaseOrder",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} - {self.total_amount} {self.currency}>"


class InvoiceLine(Base):
    """Invoice line item model.

    Represents individual line items within an invoice.
    """

    __tablename__ = "invoice_lines"
    __table_args__ = (
        Index("ix_invoice_lines_invoice_id", "invoice_id"),
        Index("ix_invoice_lines_line_number", "invoice_id", "line_number"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # Parent reference
    invoice_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Line identification
    line_number: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)

    # Product/service identification
    product_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    product_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    unit_of_measure: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Quantities and amounts
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Matching status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=LineStatus.OPEN.value,
    )

    # Matched quantities
    matched_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0"),
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="lines")
    matches: Mapped[list["InvoiceLineMatch"]] = relationship(
        "InvoiceLineMatch",
        back_populates="invoice_line",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number}: {self.description}>"

    @property
    def remaining_quantity(self) -> Decimal:
        """Calculate remaining unmatched quantity."""
        return self.quantity - self.matched_quantity


class InvoicePurchaseOrder(Base):
    """Junction table for Invoice to Purchase Order many-to-many relationship.

    Tracks which POs are associated with each invoice during matching.
    """

    __tablename__ = "invoice_purchase_orders"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    invoice_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    purchase_order_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    match_type: Mapped[str] = mapped_column(String(30), nullable=False)
    match_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    matched_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="matched_pos",
    )
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="matched_invoices",
    )

    __table_args__ = (
        Index("ix_invoice_po_unique", "invoice_id", "purchase_order_id", unique=True),
    )


class InvoiceLineMatch(Base):
    """Invoice line to PO/DN line matching details.

    Tracks the specific line-level matches between documents.
    """

    __tablename__ = "invoice_line_matches"
    __table_args__ = (
        Index("ix_invoice_line_match_invoice_line", "invoice_line_id"),
        Index("ix_invoice_line_match_po_line", "po_line_id"),
        Index("ix_invoice_line_match_dn_line", "dn_line_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    invoice_line_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("invoice_lines.id", ondelete="CASCADE"),
        nullable=False,
    )

    po_line_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("po_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    dn_line_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    cross_ref_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("cross_refs.id", ondelete="SET NULL"),
        nullable=True,
    )

    match_type: Mapped[str] = mapped_column(String(30), nullable=False)
    match_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    # Matched quantities
    invoice_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    po_quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 3), nullable=True)
    dn_quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 3), nullable=True)

    # Variance tracking
    price_variance: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 4), nullable=True
    )
    quantity_variance: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 3), nullable=True
    )

    matched_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    invoice_line: Mapped["InvoiceLine"] = relationship(
        "InvoiceLine",
        back_populates="matches",
    )


# Import at bottom to avoid circular imports
from models.purchase_order import InvoicePurchaseOrder, PurchaseOrder, POLine
from models.delivery_note import DeliveryNote, DeliveryNoteLine
