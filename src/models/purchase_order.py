// src/models/purchase_order.py
"""Purchase Order models."""
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from src.models.base import Base, BaseModel


class PurchaseOrder(Base, BaseModel):
    """Purchase Order model."""
    __tablename__ = "purchase_orders"

    po_number = Column(String(50), unique=True, nullable=False, index=True)
    supplier_id = Column(String(36), nullable=False, index=True)
    supplier_name = Column(String(255), nullable=False)
    supplier_code = Column(String(50), nullable=True)
    
    # Dates
    po_date = Column(Date, nullable=False)
    expected_delivery_date = Column(Date, nullable=True)
    
    # Status
    status = Column(String(50), default="open", nullable=False)  # open, partial, closed, cancelled
    currency = Column(String(3), default="USD", nullable=False)
    
    # Totals
    subtotal = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    tax_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    total_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    total_received = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    total_invoiced = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    
    # Notes
    notes = Column(Text, nullable=True)
    delivery_address = Column(Text, nullable=True)
    terms = Column(String(255), nullable=True)
    
    # Metadata
    created_by = Column(String(36), nullable=True)
    approved_by = Column(String(36), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    # Relationships
    lines: List["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    match_results: List["MatchResult"] = relationship(
        "MatchResult",
        foreign_keys="MatchResult.po_id",
        back_populates="purchase_order",
        lazy="selectin",
    )
    balance_entries: List["BalanceLedger"] = relationship(
        "BalanceLedger",
        foreign_keys="BalanceLedger.po_id",
        back_populates="purchase_order",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number}>"

    @property
    def is_open(self) -> bool:
        """Check if PO is still open."""
        return self.status in ("open", "partial")

    @property
    def remaining_balance(self) -> Decimal:
        """Calculate remaining balance."""
        return self.total_amount - self.total_received - self.total_invoiced


class PurchaseOrderLine(Base, BaseModel):
    """Purchase Order Line model."""
    __tablename__ = "purchase_order_lines"

    purchase_order_id = Column(
        String(36),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number = Column(Integer, nullable=False)
    item_code = Column(String(50), nullable=True, index=True)
    item_description = Column(String(500), nullable=False)
    quantity = Column(Numeric(15, 4), nullable=False)
    unit_of_measure = Column(String(20), default="EA", nullable=False)
    unit_price = Column(Numeric(15, 4), nullable=False)
    tax_rate = Column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    tax_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    line_total = Column(Numeric(15, 2), nullable=False)
    quantity_received = Column(Numeric(15, 4), default=Decimal("0"), nullable=False)
    quantity_invoiced = Column(Numeric(15, 4), default=Decimal("0"), nullable=False)
    
    # Status
    status = Column(String(50), default="open", nullable=False)

    # Relationships
    purchase_order: "PurchaseOrder" = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number}>"

    @property
    def remaining_quantity(self) -> Decimal:
        """Calculate remaining quantity."""
        return self.quantity - self.quantity_received - self.quantity_invoiced
