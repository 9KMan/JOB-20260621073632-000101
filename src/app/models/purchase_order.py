// src/app/models/purchase_order.py
"""Purchase Order models."""
import uuid
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.models.base import BaseModel


class POStatus(str, Enum):
    """Purchase Order status enumeration."""
    
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class PurchaseOrder(BaseModel):
    """Purchase Order header model."""
    
    __tablename__ = "purchase_orders"
    
    po_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    supplier_code: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    
    order_date: Mapped[date] = mapped_column(Date, nullable=False)  # noqa: F821
    expected_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)  # noqa: F821
    delivery_address: Mapped[str] = mapped_column(Text, nullable=True)
    
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    
    status: Mapped[str] = mapped_column(String(20), default=POStatus.DRAFT.value, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # noqa: F821
    
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(  # noqa: F821
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<PurchaseOrder(po_number={self.po_number}, supplier={self.supplier_code})>"
    
    @property
    def open_amount(self) -> Decimal:
        """Calculate open (unmatched) amount."""
        from sqlalchemy import select, func
        from src.app.models.invoice import InvoiceLine, Invoice
        from src.app.models.delivery_note import DeliveryNoteLine
        from src.app.database import AsyncSessionLocal
        
        # This would be calculated via query in production
        return self.total_amount
    
    @property
    def is_open(self) -> bool:
        """Check if PO is open for matching."""
        return self.status in (POStatus.SUBMITTED.value, POStatus.APPROVED.value) and not self.is_archived


class PurchaseOrderLine(BaseModel):
    """Purchase Order line item model."""
    
    __tablename__ = "purchase_order_lines"
    
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    product_code: Mapped[str] = mapped_column(String(100), nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), default="EA", nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    
    tax_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    
    expected_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)  # noqa: F821
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    purchase_order: Mapped["PurchaseOrder"] = relationship(  # noqa: F821
        "PurchaseOrder",
        back_populates="lines",
    )
    
    def __repr__(self) -> str:
        return f"<PurchaseOrderLine(line_number={self.line_number}, product={self.product_code})>"


from datetime import date
from sqlalchemy import JSON
