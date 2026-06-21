# models/invoice.py
"""Invoice and invoice line models."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef


class Invoice(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Invoice header model."""

    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_vendor_number", "vendor_number"),
        Index("ix_invoices_invoice_number", "invoice_number", unique=True),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_invoice_date", "invoice_date"),
    )

    vendor_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    vendor_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    invoice_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )
    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="draft",
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    source_system: Mapped[str] = mapped_column(
        String(50),
        default="manual",
        nullable=False,
    )
    external_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    is_credit_memo: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} - {self.total_amount}>"


class InvoiceLine(Base, UUIDMixin, TimestampMixin):
    """Invoice line item model."""

    __tablename__ = "invoice_lines"
    __table_args__ = (
        Index("ix_invoice_lines_invoice_id", "invoice_id"),
        Index("ix_invoice_lines_po_line_id", "po_line_id"),
    )

    invoice_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )
    line_number: Mapped[int] = mapped_column(
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    tax_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    tax_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )
    po_line_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    delivery_note_line_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_matched: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    match_confidence: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    match_score: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
    )
    balance_ledger_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="invoice_line",
        cascade="all, delete-orphan",
    )
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="invoice_line",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number} - {self.description}>"
