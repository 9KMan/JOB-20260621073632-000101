# models/purchase_order.py
"""PurchaseOrder and PurchaseOrderLine SQLAlchemy models.

Represents ERP purchase orders and their line items.
"""

import uuid
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin
from models.enums import PurchaseOrderStatus, LineStatus


class PurchaseOrder(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Purchase Order model representing ERP POs.
    
    POs are the primary anchor for invoice matching.
    """
    
    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_pos_vendor_number", "vendor_number"),
        Index("ix_pos_po_number", "po_number", unique=True),
        Index("ix_pos_status", "status"),
        Index("ix_pos_po_date", "po_date"),
        {"schema": None},
    )
    
    # External references
    vendor_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # PO identification
    po_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    
    # PO dates
    po_date: Mapped[Date] = mapped_column(Date, nullable=False)
    expected_delivery_date: Mapped[Optional[Date]] = mapped_column(Date, nullable=True)
    closed_date: Mapped[Optional[Date]] = mapped_column(Date, nullable=True)
    
    # Financial
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    
    # Status
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        String(20),
        nullable=False,
        default=PurchaseOrderStatus.DRAFT,
        index=True,
    )
    
    # Approval
    buyer_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    approver_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    approved_date: Mapped[Optional[Date]] = mapped_column(Date, nullable=True)
    
    # Shipping
    ship_to_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ship_to_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Payment terms
    payment_terms: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Source
    source_system: Mapped[str] = mapped_column(String(50), nullable=False, default="erp")
    source_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    lines: Mapped[List["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number} - {self.status.value}>"


class PurchaseOrderLine(Base, UUIDMixin, TimestampMixin):
    """Purchase Order line item model.
    
    Each PO can have multiple line items that are matched
    to invoice and delivery note lines.
    """
    
    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        Index("ix_po_lines_po_id", "po_id"),
        Index("ix_po_lines_item_number", "item_number"),
        {"schema": None},
    )
    
    # Foreign key to parent PO
    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Line details
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Product/service identification
    item_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    vendor_part_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Categorization
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    subcategory: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Quantities
    quantity_ordered: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    quantity_unit: Mapped[str] = mapped_column(String(20), nullable=False, default="EA")
    
    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    
    # Delivery tracking
    quantity_delivered: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
    )
    quantity_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
    )
    
    # Status
    status: Mapped[LineStatus] = mapped_column(
        String(20),
        nullable=False,
        default=LineStatus.OPEN,
    )
    
    # GL distribution
    gl_account: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    department_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    cost_center: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Delivery info
    promised_delivery_date: Mapped[Optional[Date]] = mapped_column(Date, nullable=True)
    
    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )
    
    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number}: {self.description[:30]}>"
