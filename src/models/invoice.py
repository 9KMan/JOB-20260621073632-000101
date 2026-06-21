# src/models/invoice.py
import uuid
import decimal
from datetime import date, datetime
from typing import Optional, List

from sqlalchemy import String, Numeric, Date, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin, UUIDMixin


class Invoice(Base, UUIDMixin, TimestampMixin):
    """Invoice model."""
    
    __tablename__ = "invoices"
    
    invoice_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    supplier_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    subtotal: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_amount: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), default=decimal.Decimal("0.00"))
    total_amount: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Foreign Keys
    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="invoices")
    line_items = relationship("InvoiceLineItem", back_populates="invoice", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number}>"


class InvoiceLineItem(Base, UUIDMixin, TimestampMixin):
    """Invoice Line Item model."""
    
    __tablename__ = "invoice_line_items"
    
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    item_code: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    unit_price: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_total: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    
    # Relationships
    invoice = relationship("Invoice", back_populates="line_items")
    
    def __repr__(self) -> str:
        return f"<InvoiceLineItem {self.line_number}: {self.item_code}>"
