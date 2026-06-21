# models/invoice.py
"""Invoice and InvoiceLine SQLAlchemy models."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import InvoiceStatus, LineStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef


class Invoice(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Invoice model representing vendor invoices."""

    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_vendor_number", "vendor_number"),
        Index("ix_invoices_invoice_number", "invoice_number"),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_invoice_date", "invoice_date"),
        Index("ix_invoices_vendor_number_invoice", "vendor_number", "invoice_number"),
    )

    vendor_number: Mapped[str] = mapped_column(String(50), nullable=False)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=False)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    currency_code: Mapped[str] = mapped_column(String(3), default="USD")
    status: Mapped[InvoiceStatus] = mapped_column(
        String(20),
        default=InvoiceStatus.PENDING,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_system: Mapped[str] = mapped_column(String(50), default="manual")
    external_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    is_credit_memo: Mapped[bool] = mapped_column(Boolean, default=False)

    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} from {self.vendor_name}>"


class InvoiceLine(UUIDMixin, TimestampMixin, Base):
    """Invoice line item model."""

    __tablename__ = "invoice_lines"
    __table_args__ = (
        Index("ix_invoice_lines_invoice_id", "invoice_id"),
        Index("ix_invoice_lines_line_number", "invoice_id", "line_number"),
    )

    invoice_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )
    line_number: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), default="EA")
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[LineStatus] = mapped_column(
        String(20),
        default=LineStatus.OPEN,
        nullable=False,
    )
    po_line_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("po_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    delivery_line_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    match_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="lines")
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
        return f"<InvoiceLine {self.line_number}: {self.description}>"

    @property
    def matched_quantity(self) -> Decimal:
        """Calculate the total matched quantity from balance ledger."""
        from sqlalchemy import select, func
        from core.database import AsyncSessionLocal

        return Decimal("0.00")
