// src/models/purchase_order.py
"""Purchase Order models."""
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
    from src.models.invoice import Invoice, InvoiceLine
    from src.models.delivery_note import DeliveryNote, DeliveryNoteLine
    from src.models.match import Match


class PurchaseOrder(BaseModel, SoftDeleteMixin):
    """Purchase Order — the single source of truth in 3-way matching."""

    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_purchase_orders_supplier_po_number", "supplier_id", "po_number", unique=True),
        Index("ix_purchase_orders_status", "status"),
        Index("ix_purchase_orders_supplier_id", "supplier_id"),
    )

    po_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    supplier_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)

    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    status: Mapped[str] = mapped_column(
        String(20),
        default="open",
        nullable=False,
        index=True,
    )  # open, partial, closed, cancelled

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata: Mapped[dict | None] = mapped_column(default=None)

    # Relationships
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    invoices: Mapped[list["Invoice"]] = relationship(back_populates="purchase_order")
    delivery_notes: Mapped[list["DeliveryNote"]] = relationship(back_populates="purchase_order")
    matches: Mapped[list["Match"]] = relationship(back_populates="purchase_order")

    @property
    def open_amount(self) -> Decimal:
        """Calculate remaining open amount after matched invoices."""
        matched = sum(inv.matched_amount for inv in self.invoices if inv.matched_amount)
        return self.total_amount - matched

    def __repr__(self) -> str:
        return f"<PurchaseOrder(id={self.id}, po_number={self.po_number})>"


class PurchaseOrderLine(BaseModel):
    """Line item in a Purchase Order."""

    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        Index("ix_purchase_order_lines_po_id", "purchase_order_id"),
    )

    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
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
    delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(back_populates="lines")

    @property
    def subtotal(self) -> Decimal:
        """Calculate line subtotal (amount before tax)."""
        return self.line_amount

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine(id={self.id}, sku={self.sku}, qty={self.quantity})>"
