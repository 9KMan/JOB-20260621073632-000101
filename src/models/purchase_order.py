// src/models/purchase_order.py
"""Purchase Order and Purchase Order Line models."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Column, String, Date, DateTime, Numeric, Integer, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from src.models.base import BaseModel


class PurchaseOrderStatus(str):
    """Purchase order status enum."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    PARTIALLY_MATCHED = "partially_matched"
    FULLY_MATCHED = "fully_matched"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class PurchaseOrder(BaseModel):
    """Purchase Order model - the anchor for 3-way matching."""

    __tablename__ = "purchase_orders"

    po_number: str = Column(String(50), unique=True, nullable=False, index=True)
    supplier_id: str = Column(String(100), nullable=False, index=True)
    supplier_name: str = Column(String(255), nullable=False)
    supplier_code: Optional[str] = Column(String(50), nullable=True)

    order_date: date = Column(Date, nullable=False)
    expected_delivery_date: Optional[date] = Column(Date, nullable=True)
    actual_delivery_date: Optional[date] = Column(Date, nullable=True)

    status: str = Column(String(20), default=PurchaseOrderStatus.DRAFT, nullable=False)
    
    currency: str = Column(String(3), default="USD", nullable=False)
    subtotal: Decimal = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    tax_amount: Decimal = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    total_amount: Decimal = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    
    paid_amount: Decimal = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    remaining_amount: Decimal = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)

    notes: Optional[str] = Column(String(1000), nullable=True)
    internal_reference: Optional[str] = Column(String(100), nullable=True)

    created_by_id: Optional[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_by_id: Optional[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at: Optional[datetime] = Column(DateTime, nullable=True)

    # Relationships
    lines = relationship("PurchaseOrderLine", back_populates="purchase_order", cascade="all, delete-orphan")
    created_by = relationship("User", foreign_keys=[created_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number}>"

    def calculate_remaining_amount(self) -> None:
        """Calculate remaining amount after matching."""
        self.remaining_amount = self.total_amount - self.paid_amount


class PurchaseOrderLine(BaseModel):
    """Purchase Order Line item model."""

    __tablename__ = "purchase_order_lines"

    purchase_order_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False
    )
    line_number: int = Column(Integer, nullable=False)
    item_code: str = Column(String(50), nullable=False)
    item_description: str = Column(String(500), nullable=False)
    quantity: Decimal = Column(Numeric(15, 4), nullable=False)
    unit_of_measure: str = Column(String(20), default="EA", nullable=False)
    unit_price: Decimal = Column(Numeric(15, 4), nullable=False)
    line_amount: Decimal = Column(Numeric(15, 2), nullable=False)
    tax_code: Optional[str] = Column(String(20), nullable=True)
    tax_rate: Decimal = Column(Numeric(5, 4), default=Decimal("0.00"), nullable=False)
    tax_amount: Decimal = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    delivered_quantity: Decimal = Column(Numeric(15, 4), default=Decimal("0.00"), nullable=False)
    invoiced_quantity: Decimal = Column(Numeric(15, 4), default=Decimal("0.00"), nullable=False)
    status: str = Column(String(20), default="open", nullable=False)

    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="lines")

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number} - {self.item_code}>"
