# models/invoice.py
"""Invoice and InvoiceLine SQLAlchemy models.

Represents AP invoices and their line items.
"""

import uuid
from decimal import Decimal
from typing import List, Optional

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
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin
from models.enums import InvoiceStatus, LineStatus


class Invoice(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Invoice model representing AP invoices.
    
    Invoices are matched against Purchase Orders and Delivery Notes.
    """
    
    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_vendor_number", "vendor_number"),
        Index("ix_invoices_invoice_number", "invoice_number", unique=True),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_invoice_date", "invoice_date"),
        Index("ix_invoices_created_at", "created_at"),
        {"schema": None},
    )
    
    # External references
    vendor_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    
    # Invoice details
    invoice_date: Mapped[Date] = mapped_column(Date, nullable=False)
    due_date: Mapped[Optional[Date]] = mapped_column(Date, nullable=True)
    received_date: Mapped[Date] = mapped_column(Date, nullable=False)
    
    # Financial
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    
    # Status and workflow
    status: Mapped[InvoiceStatus] = mapped_column(
        String(20),
        nullable=False,
        default=InvoiceStatus.DRAFT,
        index=True,
    )
    
    # Matching references
    matched_po_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    matched_delivery_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Match decision
    match_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    match_decision: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    match_decision_at: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)
    match_decided_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Metadata
    payment_terms: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    gl_account: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    department_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    cost_center: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Source tracking
    source_system: Mapped[str] = mapped_column(String(50), nullable=False, default="manual")
    source_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    internal_comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Approval workflow
    approved_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    approved_at: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)
    
    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    lines: Mapped[List["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} - {self.status.value}>"


class InvoiceLine(Base, UUIDMixin, TimestampMixin):
    """Invoice line item model.
    
    Each invoice can have multiple line items that are matched
    to corresponding PO and delivery note lines.
    """
    
    __tablename__ = "invoice_lines"
    __table_args__ = (
        Index("ix_invoice_lines_invoice_id", "invoice_id"),
        Index("ix_invoice_lines_po_line_id", "po_line_id"),
        Index("ix_invoice_lines_delivery_line_id", "delivery_line_id"),
        {"schema": None},
    )
    
    # Foreign key to parent invoice
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Line details
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Product/service identification
    item_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    vendor_part_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Quantities
    quantity_invoiced: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    quantity_unit: Mapped[str] = mapped_column(String(20), nullable=False, default="EA")
    
    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    tax_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    
    # Status
    status: Mapped[LineStatus] = mapped_column(
        String(20),
        nullable=False,
        default=LineStatus.OPEN,
    )
    
    # Matching references
    po_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    delivery_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Match details
    matched_quantity: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 3),
        nullable=True,
    )
    match_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    
    # GL distribution
    gl_account: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    department_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    cost_center: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
    )
    
    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number}: {self.description[:30]}>"
