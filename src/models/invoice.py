// src/models/invoice.py
"""Invoice and Invoice Line models."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Numeric, Date, Integer, ForeignKey, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Table, Column

from app.database import Base
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.purchase_order import PurchaseOrderLine, PurchaseOrder
    from app.models.delivery_note import DeliveryNoteLine


# Junction table for PO-Invoice lines many-to-many
purchase_order_invoice_lines = Table(
    "purchase_order_invoice_lines",
    Base.metadata,
    Column("purchase_order_line_id", String(36), ForeignKey("purchase_order_lines.id", ondelete="CASCADE"), primary_key=True),
    Column("invoice_line_id", String(36), ForeignKey("invoice_lines.id", ondelete="CASCADE"), primary_key=True),
    Index("ix_po_il_po_line", "purchase_order_line_id"),
    Index("ix_po_il_inv_line", "invoice_line_id"),
)


class Invoice(Base, BaseModel):
    """Invoice model."""

    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_inv_supplier_inv_number", "supplier_code", "invoice_number", unique=True),
        Index("ix_inv_status", "status"),
        Index("ix_inv_invoice_date", "invoice_date"),
    )

    invoice_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    supplier_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)  # PENDING, MATCHED, APPROVED, REJECTED, PAID
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Relationships
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number}>"


class InvoiceLine(Base, BaseModel):
    """Invoice Line item model."""

    __tablename__ = "invoice_lines"
    __table_args__ = (
        Index("ix_il_inv_id_line_number", "invoice_id", "line_number", unique=True),
    )

    invoice_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False
    )
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    item_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    item_description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity_invoiced: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), default="EA", nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="lines")
    matched_pos: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        secondary=purchase_order_invoice_lines,
        back_populates="matched_invoices",
    )

    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number} - {self.item_code}>"

    @property
    def line_amount(self) -> Decimal:
        """Calculate line total."""
        return self.quantity_invoiced * self.unit_price
