// src/models/delivery_note.py
"""Delivery Note models."""
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from src.models.base import Base, BaseModel


class DeliveryNote(Base, BaseModel):
    """Delivery Note model."""
    __tablename__ = "delivery_notes"

    dn_number = Column(String(50), unique=True, nullable=False, index=True)
    supplier_id = Column(String(36), nullable=False, index=True)
    supplier_name = Column(String(255), nullable=False)
    supplier_code = Column(String(50), nullable=True)
    
    # Reference to PO
    po_id = Column(String(36), ForeignKey("purchase_orders.id", ondelete="SET NULL"), nullable=True, index=True)
    po_number = Column(String(50), nullable=True, index=True)
    
    # Dates
    dn_date = Column(Date, nullable=False)
    delivery_date = Column(Date, nullable=True)
    receipt_date = Column(DateTime, nullable=True)
    
    # Status
    status = Column(String(50), default="pending", nullable=False)  # pending, matched, received, rejected
    currency = Column(String(3), default="USD", nullable=False)
    
    # Amounts
    subtotal = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    tax_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    total_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    
    # Matching info
    match_score = Column(Numeric(5, 4), nullable=True)
    match_status = Column(String(50), nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    delivery_address = Column(Text, nullable=True)
    carrier = Column(String(100), nullable=True)
    tracking_number = Column(String(100), nullable=True)
    
    # Metadata
    received_by = Column(String(36), nullable=True)
    matched_by = Column(String(36), nullable=True)

    # Relationships
    lines: List["DeliveryNoteLine"] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    po: Optional["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        foreign_keys=[po_id],
    )
    match_results: List["MatchResult"] = relationship(
        "MatchResult",
        foreign_keys="MatchResult.dn_id",
        back_populates="delivery_note",
        lazy="selectin",
    )
    balance_entries: List["BalanceLedger"] = relationship(
        "BalanceLedger",
        foreign_keys="BalanceLedger.dn_id",
        back_populates="delivery_note",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number}>"


class DeliveryNoteLine(Base, BaseModel):
    """Delivery Note Line model."""
    __tablename__ = "delivery_note_lines"

    delivery_note_id = Column(
        String(36),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number = Column(Integer, nullable=False)
    item_code = Column(String(50), nullable=True, index=True)
    item_description = Column(String(500), nullable=False)
    quantity = Column(Numeric(15, 4), nullable=False)
    unit_of_measure = Column(String(20), default="EA", nullable=False)
    unit_price = Column(Numeric(15, 4), nullable=False)  # From PO
    line_total = Column(Numeric(15, 2), nullable=False)
    
    # Reference to PO line
    po_line_id = Column(String(36), ForeignKey("purchase_order_lines.id", ondelete="SET NULL"), nullable=True)
    
    # Match info
    match_score = Column(Numeric(5, 4), nullable=True)
    
    # Status
    status = Column(String(50), default="pending", nullable=False)

    # Relationships
    delivery_note: "DeliveryNote" = relationship(
        "DeliveryNote",
        back_populates="lines",
    )
    po_line: Optional["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        foreign_keys=[po_line_id],
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number}>"
