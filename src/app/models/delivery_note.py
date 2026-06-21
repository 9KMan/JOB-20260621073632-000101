// src/app/models/delivery_note.py
"""
Delivery Note and Delivery Note Line models.
"""
from decimal import Decimal
from typing import List

from sqlalchemy import Column, String, Date, Numeric, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, UUIDPrimaryKey, TimestampMixin, SoftDeleteMixin


class DeliveryNote(Base, UUIDPrimaryKey, TimestampMixin, SoftDeleteMixin):
    """Delivery Note/Goods Receipt header."""

    __tablename__ = "delivery_notes"

    dn_number = Column(String(50), unique=True, nullable=False, index=True)
    supplier_id = Column(
        UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False
    )
    po_reference = Column(String(50), nullable=True, index=True)  # Reference to PO
    delivery_date = Column(Date, nullable=False, index=True)
    status = Column(String(50), default="pending", nullable=False, index=True)  # pending, matched, completed
    received_by = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    
    # ERP Integration
    erp_reference = Column(String(100), nullable=True, index=True)

    # Relationships
    supplier = relationship("Supplier", back_populates="delivery_notes")
    lines = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
    )
    match_results = relationship(
        "MatchResult",
        foreign_keys="MatchResult.dn_id",
        back_populates="delivery_note",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number}>"

    @property
    def total_quantity(self) -> Decimal:
        """Get total quantity delivered."""
        return sum(line.quantity for line in self.lines)


class DeliveryNoteLine(Base, UUIDPrimaryKey, TimestampMixin):
    """Delivery Note line item."""

    __tablename__ = "delivery_note_lines"

    delivery_note_id = Column(
        UUID(as_uuid=True), ForeignKey("delivery_notes.id", ondelete="CASCADE"), nullable=False
    )
    line_number = Column(Integer, nullable=False)
    product_code = Column(String(100), nullable=False, index=True)
    description = Column(String(500), nullable=False)
    quantity = Column(Numeric(15, 3), nullable=False)
    unit_of_measure = Column(String(20), default="EA", nullable=False)
    accepted_quantity = Column(Numeric(15, 3), nullable=True)
    rejected_quantity = Column(Numeric(15, 3), default=Decimal("0.000"), nullable=False)

    # Relationships
    delivery_note = relationship("DeliveryNote", back_populates="lines")

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number}: {self.product_code}>"

    @property
    def net_quantity(self) -> Decimal:
        """Get net accepted quantity."""
        return self.accepted_quantity or self.quantity
