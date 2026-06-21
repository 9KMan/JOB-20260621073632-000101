# src/models/purchase_order.py
import uuid
import decimal
from datetime import date, datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Numeric, Date, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from src.models.invoice import Invoice
    from src.models.delivery_note import DeliveryNote
    from src.models.balance import Balance


class PurchaseOrder(Base, UUIDMixin, TimestampMixin):
    """Purchase Order model."""
    
    __tablename__ = "purchase_orders"
    
    po_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    supplier_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    subtotal: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_amount: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), default=decimal.Decimal("0.00"))
    total_amount: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="OPEN", nullable=False)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    line_items = relationship("PurchaseOrderLineItem", back_populates="purchase_order", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="purchase_order")
    delivery_notes = relationship("DeliveryNote", back_populates="purchase_order")
    balances = relationship("Balance", back_populates="purchase_order", foreign_keys="Balance.purchase_order_id")
    
    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number}>"


class PurchaseOrderLineItem(Base, UUIDMixin, TimestampMixin):
    """Purchase Order Line Item model."""
    
    __tablename__ = "purchase_order_line_items"
    
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    item_code: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    unit_price: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_total: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    
    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="line_items")
    
    def __repr__(self) -> str:
        return f"<PurchaseOrderLineItem {self.line_number}: {self.item_code}>"
