// src/models/delivery_note.py
"""
FinaRo AP Automation Core Engine
Delivery Note Models
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
    from app.models.purchase_order import PurchaseOrder
    from app.models.invoice import Invoice
    from app.models.match import Match


class DeliveryNote(BaseModel):
    """
    Delivery Note model representing a goods receipt document.
    Part of the 3-way matching process.
    """
    __tablename__ = "delivery_notes"
    
    # DN Identification
    dn_number = Column(String(50), nullable=False, unique=True, index=True)
    supplier_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    supplier_name = Column(String(255), nullable=False)
    supplier_code = Column(String(50), nullable=True, index=True)
    
    # Reference Information
    po_id = Column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    supplier_dn_number = Column(String(100), nullable=True, index=True)
    
    # DN Dates
    dn_date = Column(Date, nullable=False, index=True)
    received_date = Column(Date, nullable=True, index=True)
    goods_receipt_date = Column(Date, nullable=True)
    
    # DN Status
    status = Column(
        SQLEnum(
            'CREATED', 'SHIPPED', 'IN_TRANSIT', 'RECEIVED',
            'INSPECTED', 'ACCEPTED', 'REJECTED', 'RETURNED',
            name='dn_status'
        ),
        default='CREATED',
        nullable=False,
        index=True
    )
    
    # Financial
    currency = Column(String(3), default='USD', nullable=False)
    total_amount = Column(Numeric(15, 2), default=Decimal('0.00'), nullable=False)
    
    # Transport Information
    carrier_name = Column(String(100), nullable=True)
    tracking_number = Column(String(100), nullable=True, index=True)
    vehicle_number = Column(String(50), nullable=True)
    
    # Additional Information
    notes = Column(Text, nullable=True)
    inspection_notes = Column(Text, nullable=True)
    department = Column(String(100), nullable=True, index=True)
    
    # Receiver Information
    received_by = Column(String(255), nullable=True)
    warehouse_location = Column(String(100), nullable=True)
    
    # Relationships
    po: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        foreign_keys=[po_id],
        lazy="selectin"
    )
    lines: Mapped[List["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    matches: Mapped[List["Match"]] = relationship(
        "Match",
        back_populates="delivery_note",
        foreign_keys="Match.dn_id",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<DeliveryNote(id={self.id}, dn_number='{self.dn_number}', status='{self.status}')>"
    
    @property
    def is_received(self) -> bool:
        """Check if delivery note has been received."""
        return self.status in ('RECEIVED', 'INSPECTED', 'ACCEPTED')


class DeliveryNoteLine(BaseModel):
    """
    Delivery Note Line Item model.
    Represents individual line items within a Delivery Note.
    """
    __tablename__ = "delivery_note_lines"
    
    # Foreign Key
    dn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
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
    quantity_delivered = Column(Numeric(15, 3), nullable=False, default=Decimal('0.000'))
    quantity_received = Column(Numeric(15, 3), nullable=False, default=Decimal('0.000'))
    quantity_rejected = Column(Numeric(15, 3), default=Decimal('0.000'), nullable=False)
    quantity_returned = Column(Numeric(15, 3), default=Decimal('0.000'), nullable=False)
    
    # Unit of Measure
    unit_of_measure = Column(String(20), default='EA', nullable=False)
    
    # Pricing
    unit_price = Column(Numeric(15, 4), nullable=True)
    line_total = Column(Numeric(15, 2), nullable=True)
    
    # Quality Status
    quality_status = Column(
        SQLEnum(
            'PENDING', 'INSPECTED', 'ACCEPTED', 'REJECTED',
            name='quality_status'
        ),
        default='PENDING',
        nullable=False,
        index=True
    )
    
    # Matched Quantities
    quantity_matched = Column(Numeric(15, 3), default=Decimal('0.000'), nullable=False)
    
    # Status
    status = Column(
        SQLEnum(
            'PENDING', 'PARTIAL', 'FULFILLED', 'DISPUTED',
            name='dnline_status'
        ),
        default='PENDING',
        nullable=False,
        index=True
    )
    
    # Relationship
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines"
    )
    
    def __repr__(self) -> str:
        return f"<DeliveryNoteLine(id={self.id}, dn_id={self.dn_id}, line_number={self.line_number})>"
    
    @property
    def quantity_unmatched(self) -> Decimal:
        """Calculate unmatched quantity."""
        return self.quantity_received - self.quantity_matched
    
    def calculate_received_quantity(self) -> None:
        """Calculate actual received quantity (delivered minus rejected/returned)."""
        self.quantity_received = self.quantity_delivered - self.quantity_rejected - self.quantity_returned
