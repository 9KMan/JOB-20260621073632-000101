// src/models/purchase_order.py
"""Purchase Order model."""
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
    from src.models.invoice import Invoice
    from src.models.match import Match
    from src.models.user import User


class PurchaseOrderLine(BaseModel):
    """Individual line item in a Purchase Order."""

    __tablename__ = "purchase_order_lines"

    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    sku: Mapped[str] = mapped_column(
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
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
        default=dict
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines"
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number}: {self.description[:30]}>"


class PurchaseOrder(BaseModel):
    """Purchase Order model - single source of truth for 3-way matching."""

    __tablename__ = "purchase_orders"

    po_number: Mapped[str] = mapped_column(
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
    order_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True
    )
    expected_delivery_date: Mapped[Optional[date]] = mapped_column(
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
        default="OPEN",
        nullable=False,
        index=True
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
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        order_by="PurchaseOrderLine.line_number"
    )
    created_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="purchase_orders",
        foreign_keys=[created_by]
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="purchase_order"
    )
    delivery_notes: Mapped[list["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="purchase_order"
    )
    matches: Mapped[list["Match"]] = relationship(
        "Match",
        back_populates="purchase_order"
    )
    balances: Mapped[list["Balance"]] = relationship(
        "Balance",
        back_populates="purchase_order"
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number}>"

    @property
    def open_amount(self) -> Decimal:
        """Calculate remaining open amount after matched invoices."""
        from sqlalchemy import select, func
        from src.models.invoice import Invoice
        
        # This would be calculated in service layer
        return self.total_amount

    def calculate_totals(self) -> None:
        """Recalculate line totals and header totals."""
        self.subtotal = sum(line.total_amount for line in self.lines)
        self.tax_amount = sum(line.tax_amount for line in self.lines)
        self.total_amount = self.subtotal + self.tax_amount
