// src/models/delivery_note.py
"""
Delivery Note (Goods Receipt) model
One side of the 3-way match
"""
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from decimal import Decimal

from src.models.base import UUIDModel, TimestampModel, SoftDeleteModel


class DeliveryNote(UUIDModel, TimestampModel, SoftDeleteModel):
    """Delivery Note model (Goods Receipt)"""
    __tablename__ = "delivery_notes"
    
    # Business identifiers
    dn_number = Column(String(50), unique=True, nullable=False, index=True)
    supplier_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    supplier_name = Column(String(255), nullable=False)
    supplier_code = Column(String(50), nullable=True)
    
    # Reference to PO (set during matching)
    purchase_order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id"),
        nullable=True,
        index=True
    )
    
    # Reference to Invoice (optional)
    invoice_id = Column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id"),
        nullable=True,
        index=True
    )
    
    # Dates
    dn_date = Column(DateTime(timezone=True), nullable=False)
    received_date = Column(DateTime(timezone=True), nullable=True)
    
    # Amounts
    subtotal = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    total_amount = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    currency = Column(String(3), default="USD", nullable=False)
    
    # Status tracking
    STATUS_PENDING = "pending"
    STATUS_RECEIVED = "received"
    STATUS_INSPECTED = "inspected"
    STATUS_ACCEPTED = "accepted"
    STATUS_REJECTED = "rejected"
    
    status = Column(String(50), default=STATUS_RECEIVED, nullable=False, index=True)
    
    # Receiving info
    received_by = Column(String(255), nullable=True)
    warehouse_location = Column(String(100), nullable=True)
    
    # Metadata
    notes = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Line items
    line_items = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan"
    )
    
    # Relationships
    purchase_order = relationship(
        "PurchaseOrder",
        back_populates="delivery_notes"
    )
    invoice = relationship(
        "Invoice",
        back_populates="delivery_notes"
    )
    created_by_user = relationship(
        "User",
        back_populates="created_delivery_notes",
        foreign_keys=[created_by]
    )
    match_records = relationship(
        "MatchRecord",
        back_populates="delivery_note"
    )
    balance_records = relationship(
        "BalanceLedger",
        back_populates="delivery_note"
    )
    
    def __repr__(self):
        return f"<DeliveryNote {self.dn_number}>"


class DeliveryNoteLine(UUIDModel, TimestampModel):
    """Line items for Delivery Note"""
    __tablename__ = "delivery_note_lines"
    
    delivery_note_id = Column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    line_number = Column(Integer, nullable=False)
    item_code = Column(String(100), nullable=True)
    description = Column(String(500), nullable=False)
    
    # Quantities
    ordered_quantity = Column(Numeric(15, 3), default=Decimal("0"), nullable=False)
    delivered_quantity = Column(Numeric(15, 3), default=Decimal("0"), nullable=False)
    accepted_quantity = Column(Numeric(15, 3), default=Decimal("0"), nullable=False)
    rejected_quantity = Column(Numeric(15, 3), default=Decimal("0"), nullable=False)
    
    unit_of_measure = Column(String(20), default="EA", nullable=False)
    
    # Link to PO line (optional, set during matching)
    purchase_order_line_id = Column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id"),
        nullable=True
    )
    
    # Relationship
    delivery_note = relationship(
        "DeliveryNote",
        back_populates="line_items"
    )
    
    def __repr__(self):
        return f"<DeliveryNoteLine {self.line_number} - {self.description}>"
