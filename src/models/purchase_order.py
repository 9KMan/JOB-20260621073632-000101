// src/models/purchase_order.py
"""Purchase Order and Purchase Order Line models."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Numeric, Date, Integer, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.invoice import InvoiceLine
    from app.models.delivery_note import DeliveryNoteLine


class PurchaseOrder(Base, BaseModel):
    """Purchase Order model - the source of truth for anchoring."""

    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_po_supplier_po_number", "supplier_code", "po_number", unique=True),
        Index("ix_po_status", "status"),
    )

    po_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    supplier_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    po_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="OPEN", nullable=False)  # OPEN, PARTIAL, CLOSED, CANCELLED
    notes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Relationships
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )
    matched_invoices: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        secondary="purchase_order_invoice_lines",
        back_populates="matched_pos",
    )
    matched_delivery_notes: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        secondary="purchase_order_delivery_note_lines",
        back_populates="matched_pos",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number}>"


class PurchaseOrderLine(Base, BaseModel):
    """Purchase Order Line item model."""

    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        Index("ix_pol_po_id_line_number", "purchase_order_id", "line_number", unique=True),
    )

    purchase_order_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False
    )
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    item_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    item_description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity_ordered: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    quantity_received: Mapped[Decimal] = mapped_column(Numeric(15, 3), default=Decimal("0.00"), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), default="EA", nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    expected_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder", back_populates="lines"
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number} - {self.item_code}>"

    @property
    def remaining_quantity(self) -> Decimal:
        """Calculate remaining quantity not yet received."""
        return self.quantity_ordered - self.quantity_received

    @property
    def line_amount(self) -> Decimal:
        """Calculate line total."""
        return self.quantity_ordered * self.unit_price
