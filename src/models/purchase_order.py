// src/models/purchase_order.py
"""
Purchase Order model
The PO is the single source of truth for 3-way matching
"""
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from decimal import Decimal
from datetime import datetime, timezone

from src.models.base import UUIDModel, TimestampModel, SoftDeleteModel


class PurchaseOrder(UUIDModel, TimestampModel, SoftDeleteModel):
    """Purchase Order model - Source of truth for matching"""
    __tablename__ = "purchase_orders"
    
    # Business identifiers
    po_number = Column(String(50), unique=True, nullable=False, index=True)
    supplier_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    supplier_name = Column(String(255), nullable=False)
    supplier_code = Column(String(50), nullable=True)
    
    # Dates
    po_date = Column(DateTime(timezone=True), nullable=False)
    expected_delivery_date = Column(DateTime(timezone=True), nullable=True)
    
    # Amounts
    total_amount = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    currency = Column(String(3), default="USD", nullable=False)
    
    # Status tracking
    STATUS_DRAFT = "draft"
    STATUS_OPEN = "open"
    STATUS_PARTIALLY_RECEIVED = "partially_received"
    STATUS_FULLY_RECEIVED = "fully_received"
    STATUS_CLOSED = "closed"
    STATUS_CANCELLED = "cancelled"
    
    status = Column(String(50), default=STATUS_OPEN, nullable=False, index=True)
    
    # Metadata
    notes = Column(Text, nullable=True)
    terms_and_conditions = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Line items
    line_items = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan"
    )
    
    # Relationships
    created_by_user = relationship(
        "User",
        back_populates="created_purchase_orders",
        foreign_keys=[created_by]
    )
    invoices = relationship(
        "Invoice",
        back_populates="purchase_order"
    )
    delivery_notes = relationship(
        "DeliveryNote",
        back_populates="purchase_order"
    )
    match_records = relationship(
        "MatchRecord",
        back_populates="purchase_order"
    )
    balance_records = relationship(
        "BalanceLedger",
        back_populates="purchase_order"
    )
    
    @property
    def open_amount(self) -> Decimal:
        """Calculate remaining open amount"""
        from sqlalchemy import select, func
        # This would be calculated dynamically
        return self.total_amount
    
    def __repr__(self):
        return f"<PurchaseOrder {self.po_number}>"


class PurchaseOrderLine(UUIDModel, TimestampModel):
    """Line items for Purchase Order"""
    __tablename__ = "purchase_order_lines"
    
    purchase_order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    line_number = Column(Integer, nullable=False)
    item_code = Column(String(100), nullable=True)
    description = Column(String(500), nullable=False)
    quantity = Column(Numeric(15, 3), nullable=False, default=Decimal("0"))
    unit_of_measure = Column(String(20), default="EA", nullable=False)
    unit_price = Column(Numeric(15, 4), nullable=False, default=Decimal("0"))
    line_amount = Column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    tax_rate = Column(Numeric(5, 4), default=Decimal("0"), nullable=False)
    tax_amount = Column(Numeric(15, 2), default=Decimal("0"), nullable=False)
    
    # Relationship
    purchase_order = relationship(
        "PurchaseOrder",
        back_populates="line_items"
    )
    
    def __repr__(self):
        return f"<PurchaseOrderLine {self.line_number} - {self.description}>"
