// src/models/delivery_note.py
"""Delivery Note models."""
from decimal import Decimal

from sqlalchemy import Column, String, Text, Numeric, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from src.models.base import BaseModel


class DeliveryNoteStatus(str, enum.Enum):
    """Delivery Note status."""
    DRAFT = "draft"
    ISSUED = "issued"
    PARTIALLY_RECEIVED = "partially_received"
    FULLY_RECEIVED = "fully_received"
    CANCELLED = "cancelled"


class DeliveryNote(BaseModel):
    """Delivery Note header."""

    __tablename__ = "delivery_notes"

    dn_number = Column(String(100), nullable=False, index=True)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    po_reference = Column(String(50), nullable=True, index=True)  # Reference to PO number
    status = Column(Integer, default=DeliveryNoteStatus.ISSUED.value, nullable=False, index=True)
    issue_date = Column(Text, nullable=False)  # ISO date string
    received_date = Column(Text, nullable=True)
    currency = Column(String(3), default="USD", nullable=False)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True)

    # Relationships
    supplier = relationship("Supplier", back_populates="delivery_notes")
    lines = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    match_records = relationship(
        "MatchRecord",
        foreign_keys="MatchRecord.dn_id",
        back_populates="delivery_note",
        lazy="dynamic",
    )


class DeliveryNoteLine(BaseModel):
    """Delivery Note line item."""

    __tablename__ = "delivery_note_lines"

    dn_id = Column(UUID(as_uuid=True), ForeignKey("delivery_notes.id"), nullable=False)
    line_number = Column(Integer, nullable=False)
    po_line_id = Column(UUID(as_uuid=True), ForeignKey("purchase_order_lines.id"), nullable=True)
    item_code = Column(String(100), nullable=True)
    description = Column(Text, nullable=False)
    quantity = Column(Numeric(15, 3), default=Decimal("0.000"), nullable=False)
    unit_of_measure = Column(String(20), default="EA", nullable=False)
    notes = Column(Text, nullable=True)

    # Relationships
    delivery_note = relationship("DeliveryNote", back_populates="lines")
    po_line = relationship("PurchaseOrderLine")
