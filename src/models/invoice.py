// src/models/invoice.py
"""Invoice and Invoice Line models."""
from decimal import Decimal
from datetime import date
from sqlalchemy import String, Numeric, Integer, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional, TYPE_CHECKING

from src.models.base import BaseModel
from src.models.enums import DocumentStatus, document_status_enum

if TYPE_CHECKING:
    from src.models.supplier import Supplier
    from src.models.purchase_order import PurchaseOrder
    from src.models.delivery_note import DeliveryNote
    from src.models.matching import Match, BalanceEntry


class Invoice(BaseModel):
    """Invoice header model."""
    
    __tablename__ = "invoices"
    
    invoice_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )
    
    supplier_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    
    po_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    invoice_date: Mapped[date] = mapped_column(
        Date(timezone=True),
        nullable=False,
        index=True
    )
    
    due_date: Mapped[date] = mapped_column(
        Date(timezone=True),
        nullable=True
    )
    
    status: Mapped[DocumentStatus] = mapped_column(
        document_status_enum,
        default=DocumentStatus.DRAFT,
        nullable=False,
        index=True
    )
    
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False
    )
    
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False
    )
    
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False
    )
    
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False
    )
    
    notes: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True
    )
    
    # Relationships
    supplier: Mapped["Supplier"] = relationship(
        "Supplier",
        back_populates="invoices"
    )
    
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        foreign_keys=[po_id],
        lazy="joined"
    )
    
    lines: Mapped[List["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="joined"
    )
    
    matched_delivery_notes: Mapped[List["Match"]] = relationship(
        "Match",
        back_populates="invoice",
        foreign_keys="Match.invoice_id",
        lazy="dynamic"
    )
    
    balance_entries: Mapped[List["BalanceEntry"]] = relationship(
        "BalanceEntry",
        back_populates="invoice",
        foreign_keys="BalanceEntry.invoice_id",
        lazy="dynamic"
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_invoices_supplier_status", "supplier_id", "status"),
        Index("ix_invoices_invoice_date", "invoice_date"),
        Index("ix_invoices_po_id", "po_id"),
    )
    
    def __repr__(self) -> str:
        return f"<Invoice(id={self.id}, invoice_number={self.invoice_number})>"


class InvoiceLine(BaseModel):
    """Invoice line item model."""
    
    __tablename__ = "invoice_lines"
    
    invoice_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    
    product_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )
    
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )
    
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False
    )
    
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        default="EA",
        nullable=False
    )
    
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False
    )
    
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False
    )
    
    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines"
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_invoice_lines_invoice_product", "invoice_id", "product_code"),
    )
    
    def __repr__(self) -> str:
        return f"<InvoiceLine(id={self.id}, line_number={self.line_number}, product={self.product_code})>"
