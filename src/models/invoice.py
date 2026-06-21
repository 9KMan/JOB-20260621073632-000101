# src/models/invoice.py
"""Invoice model."""
from decimal import Decimal
from typing import List, TYPE_CHECKING

from sqlalchemy import Column, String, Numeric, Date, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.purchase_order import PurchaseOrder
    from src.models.matching import MatchingRecord


class Invoice(BaseModel):
    """Invoice model representing supplier invoices."""

    __tablename__ = "invoices"

    invoice_number = Column(String(100), unique=True, nullable=False, index=True)
    purchase_order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    supplier_id = Column(String(100), nullable=False, index=True)
    supplier_name = Column(String(255), nullable=False)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    total_amount = Column(Numeric(15, 2), nullable=False)
    tax_amount = Column(Numeric(15, 2), default=0, nullable=False)
    net_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    status = Column(String(50), default="pending", nullable=False, index=True)
    notes = Column(String(1000), nullable=True)

    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="invoices")
    line_items = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    matching_records = relationship("MatchingRecord", back_populates="invoice")


class InvoiceLine(BaseModel):
    """Invoice Line Item model."""

    __tablename__ = "invoice_lines"

    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    line_number = Column(Integer, nullable=False)
    item_code = Column(String(100), nullable=True)
    item_description = Column(String(500), nullable=False)
    quantity = Column(Numeric(15, 3), nullable=False)
    unit_price = Column(Numeric(15, 2), nullable=False)
    line_amount = Column(Numeric(15, 2), nullable=False)
    tax_amount = Column(Numeric(15, 2), default=0, nullable=False)
    uom = Column(String(20), nullable=True)

    # Relationships
    invoice = relationship("Invoice", back_populates="line_items")
