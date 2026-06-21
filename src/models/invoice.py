// src/models/invoice.py
"""Invoice models."""
import uuid
import decimal
from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String, Integer, Numeric, Date, ForeignKey, Index, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin, UUIDMixin, SoftDeleteMixin
from src.models.enums import DocumentStatus

if TYPE_CHECKING:
    from src.models.purchase_order import PurchaseOrderLine
    from src.models.delivery_note import DeliveryNoteLine
    from src.models.matching import MatchRecord, BalanceLedger


class Invoice(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Invoice model."""
    
    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoice_supplier_number", "supplier_id", "invoice_number", unique=True),
        Index("ix_invoice_status", "status"),
        Index("ix_invoice_invoice_date", "invoice_date"),
        Index("ix_invoice_po_id", "purchase_order_id"),
    )

    invoice_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    supplier_id: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
    )
    supplier_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    supplier_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    due_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    subtotal: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=decimal.Decimal("0.00"),
    )
    tax_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    total_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=decimal.Decimal("0.00"),
    )
    amount_paid: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )
    status: Mapped[DocumentStatus] = mapped_column(
        String(50),
        default=DocumentStatus.SUBMITTED,
        nullable=False,
        index=True,
    )
    payment_terms: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
    )
    metadata: Mapped[Optional[str]] = mapped_column(
        String(2000),
        nullable=True,
    )

    # Relationships
    lines: Mapped[List["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        foreign_keys=[purchase_order_id],
    )
    matched_records: Mapped[List["MatchRecord"]] = relationship(
        "MatchRecord",
        back_populates="invoice",
        foreign_keys="MatchRecord.invoice_id",
    )
    balance_ledger: Mapped[List["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="invoice",
        foreign_keys="BalanceLedger.invoice_id",
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number}>"


class InvoiceLine(Base, UUIDMixin, TimestampMixin):
    """Invoice Line Item model."""
    
    __tablename__ = "invoice_lines"
    __table_args__ = (
        Index("ix_il_invoice_line", "invoice_id", "line_number", unique=True),
    )

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    product_code: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    quantity: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        default="EA",
        nullable=False,
    )
    unit_price: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    line_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    tax_rate: Mapped[decimal.Decimal] = mapped_column(
        Numeric(5, 4),
        default=decimal.Decimal("0.0000"),
        nullable=False,
    )
    tax_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    is_matched: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    matched_quantity: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 4),
        default=decimal.Decimal("0.0000"),
        nullable=False,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
    )
    matched_records: Mapped[List["MatchRecord"]] = relationship(
        "MatchRecord",
        back_populates="invoice_line",
        foreign_keys="MatchRecord.invoice_line_id",
    )

    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number}: {self.product_code}>"
