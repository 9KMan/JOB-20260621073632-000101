// src/models/invoice.py
"""Invoice model."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.balance import Balance
    from src.models.delivery_note import DeliveryNote
    from src.models.match import Match
    from src.models.purchase_order import PurchaseOrder


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
    sku: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0"),
        nullable=False
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False
    )
    uom: Mapped[str] = mapped_column(
        String(20),
        default="EA",
        nullable=False
    )
    po_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True
    )
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
        default=dict
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines"
    )

    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number}: {self.description[:30]}>"


class Invoice(BaseModel):
    """Invoice model for 3-way matching."""

    __tablename__ = "invoices"

    invoice_number: Mapped[str] = mapped_column(
        String(50),
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
    supplier_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True
    )
    due_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0"),
        nullable=False
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0"),
        nullable=False
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0"),
        nullable=False
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="RECEIVED",
        nullable=False,
        index=True
    )
    payment_status: Mapped[str] = mapped_column(
        String(20),
        default="UNPAID",
        nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
        default=dict
    )
    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Relationships
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        order_by="InvoiceLine.line_number"
    )
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="invoices"
    )
    matches: Mapped[list["Match"]] = relationship(
        "Match",
        back_populates="invoice"
    )
    delivery_notes: Mapped[list["DeliveryNote"]] = relationship(
        "Invoice",
        secondary="match_invoice_delivery_notes",
        back_populates="invoices"
    )
    balances: Mapped[list["Balance"]] = relationship(
        "Balance",
        back_populates="invoice"
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number}>"

    def calculate_totals(self) -> None:
        """Recalculate line totals and header totals."""
        self.subtotal = sum(line.total_amount for line in self.lines)
        self.tax_amount = sum(line.tax_amount for line in self.lines)
        self.total_amount = self.subtotal + self.tax_amount
