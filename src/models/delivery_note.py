// src/models/delivery_note.py
"""Delivery Note and Delivery Note Line models."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Column, String, Date, DateTime, Numeric, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.models.base import BaseModel


class DeliveryNoteStatus(str):
    """Delivery note status enum."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PARTIALLY_RECEIVED = "partially_received"
    FULLY_RECEIVED = "fully_received"
    MATCHING = "matching"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class DeliveryNote(BaseModel):
    """Delivery Note model - one of the three documents in 3-way matching."""

    __tablename__ = "delivery_notes"

    delivery_note_number: str = Column(String(50), unique=True, nullable=False, index=True)
    supplier_id: str = Column(String(100), nullable=False, index=True)
    supplier_name: str = Column(String(255), nullable=False)
    supplier_code: Optional[str] = Column(String(50), nullable=True)

    delivery_date: date = Column(Date, nullable=False)
    received_date: Optional[date] = Column(Date, nullable=True)
    status: str = Column(String(20), default=DeliveryNoteStatus.SUBMITTED, nullable=False)

    po_reference: Optional[str] = Column(String(50), nullable=True, index=True)
    po_id: Optional[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=True)

    waybill_number: Optional[str] = Column(String(100), nullable=True)
    carrier_name: Optional[str] = Column(String(255), nullable=True)

    notes: Optional[str] = Column(Text, nullable=True)
    rejection_reason: Optional[str] = Column(Text, nullable=True)

    created_by_id: Optional[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    received_by_id: Optional[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_by_id: Optional[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at: Optional[datetime] = Column(DateTime, nullable=True)

    # Relationships
    lines = relationship("DeliveryNoteLine", back_populates="delivery_note", cascade="all, delete-orphan")
    purchase_order = relationship("PurchaseOrder", foreign_keys=[po_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    received_by = relationship("User", foreign_keys=[received_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.delivery_note_number}>"


class DeliveryNoteLine(BaseModel):
    """Delivery Note Line item model."""

    __tablename__ = "delivery_note_lines"

    delivery_note_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("delivery_notes.id", ondelete="CASCADE"), nullable=False
    )
    line_number: int = Column(Integer, nullable=False)
    item_code: str = Column(String(50), nullable=False)
    item_description: str = Column(String(500), nullable=False)
    ordered_quantity: Decimal = Column(Numeric(15, 4), default=Decimal("0.00"), nullable=False)
    delivered_quantity: Decimal = Column(Numeric(15, 4), nullable=False)
    accepted_quantity: Decimal = Column(Numeric(15, 4), default=Decimal("0.00"), nullable=False)
    rejected_quantity: Decimal = Column(Numeric(15, 4), default=Decimal("0.00"), nullable=False)
    unit_of_measure: str = Column(String(20), default="EA", nullable=False)

    # Link to PO line for matching
    po_line_id: Optional[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("purchase_order_lines.id"), nullable=True)
    matched_quantity: Decimal = Column(Numeric(15, 4), default=Decimal("0.00"), nullable=False)

    notes: Optional[str] = Column(Text, nullable=True)

    # Relationships
    delivery_note = relationship("DeliveryNote", back_populates="lines")
    po_line = relationship("PurchaseOrderLine", foreign_keys=[po_line_id])

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number} - {self.item_code}>"
