// src/models/purchase_order.py
"""
FinaRo AP Automation Core Engine
Purchase Order Models
"""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import Column, String, Date, DateTime, Numeric, Integer, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.invoice import Invoice
    from app.models.delivery_note import DeliveryNote
    from app.models.match import Match


class PurchaseOrder(BaseModel):
    """
    Purchase Order model representing a PO document.
    Acts as the single source of truth in the 3-way matching process.
    """
    __tablename__ = "purchase_orders"
    
    # PO Identification
    po_number = Column(String(50), unique=True, nullable=False, index=True)
    supplier_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    supplier_name = Column(String(255), nullable=False)
    supplier_code = Column(String(50), nullable=True, index=True)
    
    # Company Information
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    company_name = Column(String(255), nullable=False)
    
    # PO Dates
    po_date = Column(Date, nullable=False, index=True)
    expected_delivery_date = Column(Date, nullable=True)
    latest_delivery_date = Column(Date, nullable=True)
    
    # PO Status
    status = Column(
        SQLEnum(
            'DRAFT', 'PENDING', 'APPROVED', 'ORDERED', 'PARTIALLY_RECEIVED',
            'RECEIVED', 'CLOSED', 'CANCELLED', name='po_status'
        ),
        default='DRAFT',
        nullable=False,
        index=True
    )
    
    # Financial
    currency = Column(String(3), default='USD', nullable=False)
    subtotal = Column(Numeric(15, 2), default=Decimal('0.00'), nullable=False)
    tax_amount = Column(Numeric(15, 2), default=Decimal('0.00'), nullable=False)
    total_amount = Column(Numeric(15, 2), default=Decimal('0.00'), nullable=False)
    
    # Terms
    payment_terms = Column(String(100), nullable=True)
    delivery_terms = Column(String(100), nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)
    
    # Metadata
    department = Column(String(100), nullable=True, index=True)
    cost_center = Column(String(50), nullable=True, index=True)
    
    # Relationships
    lines: Mapped[List["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    matches_as_anchor: Mapped[List["Match"]] = relationship(
        "Match",
        foreign_keys="Match.po_id",
        back_populates="po",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<PurchaseOrder(id={self.id}, po_number='{self.po_number}', status='{self.status}')>"
    
    @property
    def open_amount(self) -> Decimal:
        """Calculate the open (unmatched) amount of the PO."""
        from sqlalchemy import func
        from app.models.invoice import InvoiceLine
        from app.models.delivery_note import DeliveryNoteLine
        
        # This would typically be calculated via a query
        # For now, return total as placeholder
        return self.total_amount
    
    @property
    def is_open(self) -> bool:
        """Check if PO is still open for matching."""
        return self.status in ('APPROVED', 'ORDERED', 'PARTIALLY_RECEIVED')


class PurchaseOrderLine(BaseModel):
    """
    Purchase Order Line Item model.
    Represents individual line items within a Purchase Order.
    """
    __tablename__ = "purchase_order_lines"
    
    # Foreign Key
    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Line Identification
    line_number = Column(Integer, nullable=False)
    internal_reference = Column(String(100), nullable=True)
    
    # Product/Service Information
    product_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    product_code = Column(String(50), nullable=True, index=True)
    product_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Quantities
    quantity_ordered = Column(Numeric(15, 3), nullable=False, default=Decimal('0.000'))
    quantity_received = Column(Numeric(15, 3), nullable=False, default=Decimal('0.000'))
    quantity_invoiced = Column(Numeric(15, 3), nullable=False, default=Decimal('0.000'))
    
    # Unit of Measure
    unit_of_measure = Column(String(20), default='EA', nullable=False)
    
    # Pricing
    unit_price = Column(Numeric(15, 4), nullable=False, default=Decimal('0.0000'))
    line_total = Column(Numeric(15, 2), nullable=False, default=Decimal('0.00'))
    tax_rate = Column(Numeric(5, 4), default=Decimal('0.0000'), nullable=False)
    tax_amount = Column(Numeric(15, 2), default=Decimal('0.00'), nullable=False)
    
    # Dates
    expected_delivery_date = Column(Date, nullable=True)
    
    # Status
    status = Column(
        SQLEnum(
            'PENDING', 'PARTIAL', 'FULFILLED', 'CANCELLED',
            name='poline_status'
        ),
        default='PENDING',
        nullable=False,
        index=True
    )
    
    # Relationship
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines"
    )
    
    def __repr__(self) -> str:
        return f"<PurchaseOrderLine(id={self.id}, po_id={self.po_id}, line_number={self.line_number})>"
    
    @property
    def quantity_remaining(self) -> Decimal:
        """Calculate remaining quantity to be delivered."""
        return self.quantity_ordered - self.quantity_received
    
    @property
    def amount_remaining(self) -> Decimal:
        """Calculate remaining amount to be invoiced."""
        return self.line_total - (self.unit_price * self.quantity_invoiced)
    
    def calculate_totals(self) -> None:
        """Calculate line totals based on quantity and unit price."""
        self.line_total = self.quantity_ordered * self.unit_price
        self.tax_amount = self.line_total * self.tax_rate
