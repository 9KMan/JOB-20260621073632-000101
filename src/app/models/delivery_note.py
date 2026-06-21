// src/app/models/delivery_note.py
"""Delivery Note and Delivery Note Line models."""

from sqlalchemy import Column, String, Numeric, Integer, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from src.app.models.base import BaseModel


class DeliveryNote(BaseModel):
    """Delivery Note header entity."""

    __tablename__ = "delivery_notes"

    dn_number = Column(String(50), unique=True, nullable=False, index=True)
    po_reference = Column(String(50), nullable=True, index=True)
    supplier_id = Column(
        UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False
    )
    delivery_date = Column(Date, nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False, default=0)
    currency = Column(String(3), nullable=False, default="USD")
    status = Column(String(20), nullable=False, default="RECEIVED")
    notes = Column(String(1000), nullable=True)

    # Relationships
    supplier = relationship("Supplier", back_populates="delivery_notes")
    lines = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote(id={self.id}, dn_number={self.dn_number})>"


class DeliveryNoteLine(BaseModel):
    """Delivery Note line item entity."""

    __tablename__ = "delivery_note_lines"

    delivery_note_id = Column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
    )
    line_number = Column(Integer, nullable=False)
    item_code = Column(String(50), nullable=False)
    description = Column(String(500), nullable=True)
    quantity = Column(Numeric(12, 3), nullable=False)
    unit_price = Column(Numeric(15, 4), nullable=True)
    line_total = Column(Numeric(15, 2), nullable=False)
    uom = Column(String(20), nullable=True)

    # Relationships
    delivery_note = relationship("DeliveryNote", back_populates="lines")

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine(id={self.id}, line_number={self.line_number})>"
