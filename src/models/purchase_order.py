# src/models/purchase_order.py
"""Purchase Order model."""
from decimal import Decimal
from typing import List, TYPE_CHECKING

from sqlalchemy import Column, String, Numeric, Date, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.models.base import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from src.models.match_result import MatchResult
    from src.models.balance_ledger import BalanceLedger


class PurchaseOrder(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Purchase Order model - Single source of truth for anchoring."""
    
    __tablename__ = "purchase_orders"
    
    po_number = Column(String(50), unique=True, nullable=False, index=True)
    supplier_id = Column(String(50), nullable=False, index=True)
    supplier_name = Column(String(255), nullable=False)
    supplier_code = Column(String(50), nullable=True)
    
    order_date = Column(Date, nullable=False)
    expected_delivery_date = Column(Date, nullable=True)
    
    currency = Column(String(3), default="USD", nullable=False)
    subtotal = Column(Numeric(15, 2), nullable=False)
    tax_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False)
    
    status = Column(
        String(20),
        default="DRAFT",
        nullable=False,
        index=True,
    )  # DRAFT, OPEN, PARTIALLY_RECEIVED, CLOSED, CANCELLED
    
    notes = Column(Text, nullable=True)
    terms_and_conditions = Column(Text, nullable=True)
    
    # Relationships
    line_items = relationship(
        "PurchaseOrderLineItem",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )
    matched_invoices = relationship(
        "MatchResult",
        foreign_keys="MatchResult.purchase_order_id",
        back_populates="purchase_order",
    )
    balance_entries = relationship(
        "BalanceLedger",
        foreign_keys="BalanceLedger.po_id",
        back_populates="purchase_order",
    )
    
    def __repr__(self) -> str:
        return f"<PurchaseOrder(id={self.id}, po_number={self.po_number})>"


class PurchaseOrderLineItem(Base, UUIDMixin, TimestampMixin):
    """Purchase Order Line Item model."""
    
    __tablename__ = "purchase_order_line_items"
    
    purchase_order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    line_number = Column(Integer, nullable=False)
    sku = Column(String(100), nullable=True, index=True)
    description = Column(String(500), nullable=False)
    
    quantity_ordered = Column(Numeric(15, 3), nullable=False)
    quantity_received = Column(Numeric(15, 3), default=Decimal("0.00"), nullable=False)
    quantity_invoiced = Column(Numeric(15, 3), default=Decimal("0.00"), nullable=False)
    
    unit_of_measure = Column(String(20), default="EA", nullable=False)
    unit_price = Column(Numeric(15, 4), nullable=False)
    line_total = Column(Numeric(15, 2), nullable=False)
    
    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="line_items")
    
    def __repr__(self) -> str:
        return f"<PurchaseOrderLineItem(id={self.id}, sku={self.sku})>"
