// src/models/purchase_order.py
"""Purchase Order and Purchase Order Line models."""
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.invoice import Invoice
    from src.models.delivery_note import DeliveryNote
    from src.models.balance import BalanceLedger
    from src.models.match import Match


class PurchaseOrderLine(BaseModel):
    """Purchase Order Line item model."""
    
    __tablename__ = "purchase_order_lines"
    
    purchase_order_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    item_code: Mapped[Optional[str]] = mapped_column(
        String(length=50),
        nullable=True,
        index=True,
    )
    description: Mapped[str] = mapped_column(
        String(length=500),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=3),
        nullable=False,
    )
    unit_of_measure: Mapped[Optional[str]] = mapped_column(
        String(length=20),
        nullable=True,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
    )
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
    )
    tax_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=5, scale=2),
        nullable=True,
    )
    expected_delivery_date: Mapped[Optional[Date]] = mapped_column(
        Date,
        nullable=True,
    )
    
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )
    
    def __repr__(self) -> str:
        return f"<POLine {self.line_number}: {self.description}>"


class PurchaseOrder(BaseModel):
    """Purchase Order model."""
    
    __tablename__ = "purchase_orders"
    
    po_number: Mapped[str] = mapped_column(
        String(length=50),
        unique=True,
        nullable=False,
        index=True,
    )
    supplier_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(length=20),
        nullable=False,
        default="OPEN",
        index=True,
    )
    order_date: Mapped[Date] = mapped_column(
        Date,
        nullable=False,
    )
    expected_delivery_date: Mapped[Optional[Date]] = mapped_column(
        Date,
        nullable=True,
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(length=3),
        nullable=False,
        default="USD",
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    created_by: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    supplier: Mapped["Supplier"] = relationship(
        "Supplier",
        back_populates="purchase_orders",
    )
    lines: Mapped[List["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        order_by="PurchaseOrderLine.line_number",
    )
    invoices: Mapped[List["Invoice"]] = relationship(
        "Invoice",
        back_populates="purchase_order",
    )
    delivery_notes: Mapped[List["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="purchase_order",
    )
    matches: Mapped[List["Match"]] = relationship(
        "Match",
        back_populates="purchase_order",
    )
    balance_entries: Mapped[List["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="purchase_order",
    )
    
    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number}>"


# Import for type hints
from src.models.user import User
