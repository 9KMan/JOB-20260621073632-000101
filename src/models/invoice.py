// src/models/invoice.py
"""Invoice models."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.models.base import BaseModel, SoftDeleteMixin

if TYPE_CHECKING:
    from src.models.purchase_order import PurchaseOrder, PurchaseOrderLine
    from src.models.delivery_note import DeliveryNote, DeliveryNoteLine
    from src.models.match import Match


class Invoice(BaseModel, SoftDeleteMixin):
    """Invoice from a supplier."""

    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_supplier_invoice_number", "supplier_id", "invoice_number", unique=True),
        Index("ix_invoices_supplier_id", "supplier_id"),
        Index("ix_invoices_purchase_order_id", "purchase_order_id"),
        Index("ix_invoices_status", "status"),
    )

    invoice_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    supplier_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)

    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    received_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)

    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        index=True,
    )  # pending, matched, approved, rejected, paid

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata: Mapped[dict | None] = mapped_column(default=None)

    # Relationships
    purchase_order: Mapped["PurchaseOrder | None"] = relationship(back_populates="invoices")
    lines: Mapped[list["InvoiceLine"]] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    matches: Mapped[list["Match"]] = relationship(back_populates="invoice")

    @property
    def unmatched_amount(self) -> Decimal:
        """Calculate unmatched amount."""
        return self.total_amount - self.matched_amount

    def __repr__(self) -> str:
        return f"<Invoice(id={self.id}, invoice_number={self.invoice_number})>"


class InvoiceLine(BaseModel):
    """Line item in an Invoice."""

    __tablename__ = "invoice_lines"
    __table_args__ = (
        Index("ix_invoice_lines_invoice_id", "invoice_id"),
    )

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )

    line_number: Mapped[int] = mapped_column(nullable=False)
    sku: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), default="EA", nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)

    # Reference to PO line if matched
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    delivery_note_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    matched_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        default=Decimal("0.00"),
        nullable=False,
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(back_populates="lines")

    def __repr__(self) -> str:
        return f"<InvoiceLine(id={self.id}, sku={self.sku}, qty={self.quantity})>"
