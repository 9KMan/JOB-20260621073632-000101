// src/app/models/purchase_order.py
"""
Purchase Order and Purchase Order Line models.
"""
from decimal import Decimal
from typing import List

from sqlalchemy import Column, String, Date, Numeric, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, UUIDPrimaryKey, TimestampMixin, SoftDeleteMixin


class PurchaseOrder(Base, UUIDPrimaryKey, TimestampMixin, SoftDeleteMixin):
    """Purchase Order header."""

    __tablename__ = "purchase_orders"

    po_number = Column(String(50), unique=True, nullable=False, index=True)
    supplier_id = Column(
        UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False
    )
    order_date = Column(Date, nullable=False, index=True)
    expected_delivery_date = Column(Date, nullable=True)
    status = Column(String(50), default="open", nullable=False, index=True)  # open, partial, closed, cancelled
    currency = Column(String(3), default="USD", nullable=False)
    subtotal = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    tax_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    total_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    notes = Column(Text, nullable=True)
    
    # ERP Integration
    erp_reference = Column(String(100), nullable=True, index=True)

    # Relationships
    supplier = relationship("Supplier", back_populates="purchase_orders")
    lines = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )
    matched_invoices = relationship(
        "MatchResult",
        foreign_keys="MatchResult.po_id",
        back_populates="purchase_order",
    )
    matched_delivery_notes = relationship(
        "MatchResult",
        foreign_keys="MatchResult.dn_id",
        back_populates="delivery_note",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number}>"

    @property
    def is_open(self) -> bool:
        """Check if PO is open."""
        return self.status == "open"

    @property
    def open_amount(self) -> Decimal:
        """Calculate remaining open amount."""
        return self.total_amount


class PurchaseOrderLine(Base, UUIDPrimaryKey, TimestampMixin):
    """Purchase Order line item."""

    __tablename__ = "purchase_order_lines"

    purchase_order_id = Column(
        UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False
    )
    line_number = Column(Integer, nullable=False)
    product_code = Column(String(100), nullable=False, index=True)
    description = Column(String(500), nullable=False)
    quantity = Column(Numeric(15, 3), nullable=False)
    unit_of_measure = Column(String(20), default="EA", nullable=False)
    unit_price = Column(Numeric(15, 4), nullable=False)
    line_total = Column(Numeric(15, 2), nullable=False)
    expected_delivery_date = Column(Date, nullable=True)

    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="lines")

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number}: {self.product_code}>"
