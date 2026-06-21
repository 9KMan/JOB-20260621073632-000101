// src/models/invoice.py
"""Invoice models."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Integer, Numeric, Date, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel, SoftDeleteMixin

if TYPE_CHECKING:
    from src.models.matching import MatchRecord
    from src.models.balance import BalanceLedger


class Invoice(BaseModel, SoftDeleteMixin):
    """Invoice - One of the three documents in 3-way matching."""
    
    __tablename__ = "invoices"
    
    invoice_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )
    
    supplier_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )
    
    supplier_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    
    po_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True
    )
    
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="PENDING"
    )
    
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD"
    )
    
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False
    )
    
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0")
    )
    
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False
    )
    
    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )
    
    due_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True
    )
    
    # Relationships
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        order_by="InvoiceLine.line_number"
    )
    
    match_records: Mapped[list["MatchRecord"]] = relationship(
        "MatchRecord",
        back_populates="invoice"
    )
    
    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number}>"


class InvoiceLine(BaseModel):
    """Individual line item in an Invoice."""
    
    __tablename__ = "invoice_lines"
    
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    
    sku: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False
    )
    
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False
    )
    
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False
    )
    
    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines"
    )
    
    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number}: {self.sku}>"
