// src/models/purchase_order.py
"""Purchase Order models."""
from decimal import Decimal
from enum import Enum
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, String, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel, TimestampMixin


class POStatus(str, Enum):
    """Purchase order status."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CANCELLED = "cancelled"
    CLOSED = "closed"


class PurchaseOrder(BaseModel, TimestampMixin):
    """Purchase order model."""
    
    __tablename__ = "purchase_orders"
    
    po_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    supplier_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    supplier_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    order_date: Mapped[str] = mapped_column(String(10), nullable=False)
    expected_delivery_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    
    status: Mapped[POStatus] = mapped_column(
        SQLEnum(POStatus, name="po_status", create_type=False),
        default=POStatus.DRAFT,
        nullable=False,
    )
    
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata: Mapped[dict | None] = mapped_column(Text, nullable=True)
    
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number}>"


class PurchaseOrderLine(BaseModel, TimestampMixin):
    """Purchase order line item model."""
    
    __tablename__ = "purchase_order_lines"
    
    purchase_order_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    line_number: Mapped[int] = mapped_column(nullable=False)
    sku: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), default="EA", nullable=False)
    
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.00"), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    
    received_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=Decimal("0.00"), nullable=False)
    invoiced_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=Decimal("0.00"), nullable=False)
    
    metadata: Mapped[dict | None] = mapped_column(Text, nullable=True)
    
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        back_populates="lines",
    )
    
    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number}: {self.description}>"
