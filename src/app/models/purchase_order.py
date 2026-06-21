// src/app/models/purchase_order.py
"""Purchase Order model."""
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.models.base import BaseModel

if TYPE_CHECKING:
    from src.app.models.invoice import Invoice
    from src.app.models.delivery_note import DeliveryNote
    from src.app.models.user import User


class PurchaseOrder(BaseModel):
    """Purchase Order model - the anchor for 3-way matching."""

    __tablename__ = "purchase_orders"

    po_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    supplier_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    supplier_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    order_date: Mapped["date"] = mapped_column(
        type_=Date,
        nullable=False,
    )
    expected_delivery_date: Mapped["date | None"] = mapped_column(
        type_=Date,
        nullable=True,
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="OPEN",
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    created_by_user: Mapped["User | None"] = relationship(
        back_populates="purchase_orders",
        foreign_keys=[created_by],
    )
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        back_populates="purchase_order",
        foreign_keys="Invoice.po_id",
    )
    delivery_notes: Mapped[list["DeliveryNote"]] = relationship(
        back_populates="purchase_order",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number}>"


class PurchaseOrderLine(BaseModel):
    """Purchase Order Line Item."""

    __tablename__ = "purchase_order_lines"

    po_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    item_code: Mapped[str] = mapped_column(
        String(100),
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
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="EA",
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    expected_delivery_date: Mapped["date | None"] = mapped_column(
        type_=Date,
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        back_populates="lines",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number}>"


# Import Date and uuid at module level
from datetime import date
import uuid
