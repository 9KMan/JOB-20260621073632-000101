// src/models/invoice.py
"""Invoice and Invoice Line models."""
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.purchase_order import PurchaseOrder
    from src.models.balance import BalanceLedger
    from src.models.match import Match


class InvoiceLine(BaseModel):
    """Invoice Line item model."""
    
    __tablename__ = "invoice_lines"
    
    invoice_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    item_code: Mapped[Optional[str]] = mapped_column(
        String(length=50),
        nullable=True,
        index=True,
    )
    description: Mapped[str] = mapped_column(
        String(length=500),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=3),
        nullable=False,
    )
    unit_of_measure: Mapped[Optional[str]] = mapped_column(
        String(length=20),
        nullable=True,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
    )
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
    )
    tax_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=5, scale=2),
        nullable=True,
    )
    
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
    )
    
    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number}: {self.description}>"


class Invoice(BaseModel):
    """Invoice model."""
    
    __tablename__ = "invoices"
    
    invoice_number: Mapped[str] = mapped_column(
        String(length=50),
        unique=True,
        nullable=False,
        index=True,
    )
    supplier_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    po_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(length=20),
        nullable=False,
        default="PENDING",
        index=True,
    )
    invoice_date: Mapped[Date] = mapped_column(
        Date,
        nullable=False,
    )
    due_date: Mapped[Optional[Date]] = mapped_column(
        Date,
        nullable=True,
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
    )
    tax_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=True,
    )
    currency: Mapped[str] = mapped_column(
        String(length=3),
        nullable=False,
        default="USD",
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    created_by: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    supplier: Mapped["Supplier"] = relationship(
        "Supplier",
        back_populates="invoices",
    )
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="invoices",
    )
    lines: Mapped[List["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        order_by="InvoiceLine.line_number",
    )
    matches: Mapped[List["Match"]] = relationship(
        "Match",
        back_populates="invoice",
    )
    balance_entries: Mapped[List["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="invoice",
    )
    
    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number}>"
