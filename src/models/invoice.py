// src/models/invoice.py
"""Invoice and Invoice Line models."""
import uuid
import decimal
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    String,
    Date,
    DateTime,
    Numeric,
    Integer,
    ForeignKey,
    Text,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel, SoftDeleteMixin
from src.models.enums import DocumentStatus

if TYPE_CHECKING:
    from src.models.supplier import Supplier
    from src.models.match import MatchLine, BalanceLedger


class Invoice(BaseModel, SoftDeleteMixin):
    """Invoice header from supplier."""

    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoice_supplier_status", "supplier_id", "status"),
        Index("ix_invoice_number", "invoice_number"),
    )

    invoice_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    po_reference: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )
    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    due_date: Mapped[date] = mapped_column(
        Date,
        nullable=True,
    )
    status: Mapped[DocumentStatus] = mapped_column(
        DocumentStatus.enum,
        default=DocumentStatus.SUBMITTED,
        nullable=False,
    )
    subtotal: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    tax_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    total_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )
    payment_terms: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
    )
    notes: Mapped[str] = mapped_column(
        Text,
        nullable=True,
    )
    attachment_url: Mapped[str] = mapped_column(
        String(500),
        nullable=True,
    )

    # Relationships
    supplier: Mapped["Supplier"] = relationship(
        "Supplier",
        back_populates="invoices",
    )
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )
    matched_lines: Mapped[list["MatchLine"]] = relationship(
        "MatchLine",
        back_populates="invoice_line",
        foreign_keys="MatchLine.invoice_line_id",
    )
    balance_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="invoice",
        foreign_keys="BalanceLedger.invoice_id",
    )

    def calculate_totals(self) -> None:
        """Calculate subtotal, tax, and total amounts from lines."""
        self.subtotal = sum((line.line_total for line in self.lines), decimal.Decimal("0.00"))
        self.tax_amount = sum((line.tax_amount for line in self.lines), decimal.Decimal("0.00"))
        self.total_amount = self.subtotal + self.tax_amount

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number}>"


class InvoiceLine(BaseModel):
    """Invoice Line Item."""

    __tablename__ = "invoice_lines"
    __table_args__ = (
        Index("ix_il_invoice_line", "invoice_id", "line_number", unique=True),
    )

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
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
    line_total: Mapped[decimal.Decimal] = mapped_column(
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

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
    )
    matched_lines: Mapped[list["MatchLine"]] = relationship(
        "MatchLine",
        back_populates="invoice_line",
        foreign_keys="MatchLine.invoice_line_id",
    )

    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number}: {self.product_code}>"

    def calculate_totals(self) -> None:
        """Calculate line total from quantity and unit price."""
        self.line_total = self.quantity * self.unit_price
        self.tax_amount = self.line_total * self.tax_rate
