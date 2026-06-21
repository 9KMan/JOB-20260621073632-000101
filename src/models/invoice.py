// src/models/invoice.py
"""Invoice models."""
from decimal import Decimal
from enum import Enum
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, String, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel, TimestampMixin


class InvoiceStatus(str, Enum):
    """Invoice status."""
    DRAFT = "draft"
    PENDING = "pending"
    MATCHING = "matching"
    MATCHED = "matched"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class Invoice(BaseModel, TimestampMixin):
    """Invoice model."""
    
    __tablename__ = "invoices"
    
    invoice_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    supplier_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    supplier_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    po_reference: Mapped[str | None] = mapped_column(String(50), index=True, nullable=True)
    
    invoice_date: Mapped[str] = mapped_column(String(10), nullable=False)
    due_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    
    status: Mapped[InvoiceStatus] = mapped_column(
        SQLEnum(InvoiceStatus, name="invoice_status", create_type=False),
        default=InvoiceStatus.DRAFT,
        nullable=False,
    )
    
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata: Mapped[dict | None] = mapped_column(Text, nullable=True)
    
    lines: Mapped[list["InvoiceLine"]] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number}>"


class InvoiceLine(BaseModel, TimestampMixin):
    """Invoice line item model."""
    
    __tablename__ = "invoice_lines"
    
    invoice_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    line_number: Mapped[int] = mapped_column(nullable=False)
    sku: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), default="EA", nullable=False)
    
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.00"), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    
    metadata: Mapped[dict | None] = mapped_column(Text, nullable=True)
    
    invoice: Mapped["Invoice"] = relationship(
        back_populates="lines",
    )
    
    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number}: {self.description}>"
