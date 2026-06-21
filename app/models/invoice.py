// app/models/invoice.py
// app/models/invoice.py
"""Invoice models for AP automation."""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.vendor import Vendor
    from app.models.match import Match, MatchLine
    from app.models.balance import BalanceLedger


class InvoiceStatus(str):
    """Invoice status enumeration."""
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    MATCHED = "MATCHED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class Invoice(Base):
    """Invoice model for accounts payable."""
    
    __tablename__ = "invoices"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    # Invoice identification
    invoice_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vendors.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    
    # Reference to PO
    po_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        ForeignKey("purchase_orders.po_number", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default=InvoiceStatus.DRAFT,
        nullable=False,
        index=True,
    )
    
    # Dates
    invoice_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    
    due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    
    receipt_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Currency and amounts
    currency_code: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )
    
    subtotal: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    
    tax_amount: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    
    shipping_amount: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    
    total_amount: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        index=True,
    )
    
    amount_paid: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    
    # Variance tracking
    variance_amount: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    
    # Terms
    payment_terms_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    
    payment_terms_days: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    
    # References
    reference_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Approval workflow
    approved_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    rejection_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Metadata
    created_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    source_system: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    
    source_document_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    
    # Relationships
    vendor: Mapped["Vendor"] = relationship(
        "Vendor",
        back_populates="invoices",
    )
    
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        foreign_keys=[po_number],
        overlaps="invoices,purchase_orders",
    )
    
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )
    
    matches: Mapped[list["Match"]] = relationship(
        "Match",
        back_populates="invoice",
    )
    
    balance_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="invoice",
    )
    
    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number}>"
    
    def to_dict(self, include_lines: bool = False) -> dict:
        """Convert invoice to dictionary."""
        result = {
            "id": str(self.id),
            "invoice_number": self.invoice_number,
            "vendor_id": str(self.vendor_id),
            "po_number": self.po_number,
            "status": self.status,
            "invoice_date": self.invoice_date.isoformat() if self.invoice_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "receipt_date": self.receipt_date.isoformat() if self.receipt_date else None,
            "currency_code": self.currency_code,
            "subtotal": self.subtotal,
            "tax_amount": self.tax_amount,
            "shipping_amount": self.shipping_amount,
            "total_amount": self.total_amount,
            "amount_paid": self.amount_paid,
            "variance_amount": self.variance_amount,
            "payment_terms_code": self.payment_terms_code,
            "payment_terms_days": self.payment_terms_days,
            "reference_number": self.reference_number,
            "notes": self.notes,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "rejection_reason": self.rejection_reason,
            "created_by": self.created_by,
            "source_system": self.source_system,
            "source_document_id": self.source_document_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_lines:
            result["lines"] = [line.to_dict() for line in self.lines]
        
        return result


class InvoiceLine(Base):
    """Invoice Line Item model."""
    
    __tablename__ = "invoice_lines"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    
    # Product/Service information
    sku: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    
    quantity: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    
    unit_of_measure: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    
    # Pricing
    unit_price: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    
    line_total: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    
    tax_rate: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    
    tax_amount: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    
    # Reference
    po_line_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    reference_line: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    
    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
    )
    
    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number}: {self.description[:30]}>"
    
    def to_dict(self) -> dict:
        """Convert invoice line to dictionary."""
        return {
            "id": str(self.id),
            "invoice_id": str(self.invoice_id),
            "line_number": self.line_number,
            "sku": self.sku,
            "description": self.description,
            "quantity": self.quantity,
            "unit_of_measure": self.unit_of_measure,
            "unit_price": self.unit_price,
            "line_total": self.line_total,
            "tax_rate": self.tax_rate,
            "tax_amount": self.tax_amount,
            "po_line_reference": self.po_line_reference,
            "reference_line": self.reference_line,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# Add forward reference to PurchaseOrder
from app.models.purchase_order import PurchaseOrder
