# app/models/delivery_note.py
"""Delivery Note and Delivery Note Line models."""
from sqlalchemy import Column, String, Numeric, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from app.models.base import Base, TimestampMixin


class DeliveryNoteStatus(str, enum.Enum):
    """Delivery Note status enum."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    DELIVERED = "delivered"
    PARTIALLY_DELIVERED = "partially_delivered"
    CANCELLED = "cancelled"


class DeliveryNote(Base, TimestampMixin):
    """Delivery Note model (receiving document)."""

    __tablename__ = "delivery_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dn_number = Column(String(50), unique=True, nullable=False, index=True)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False)
    po_reference = Column(String(50), nullable=True, index=True)
    status = Column(String(20), default=DeliveryNoteStatus.SUBMITTED.value, nullable=False, index=True)
    delivery_date = Column(String(20), nullable=False)  # ISO date string
    received_by = Column(String(255), nullable=True)
    currency = Column(String(3), default="USD", nullable=False)
    subtotal = Column(Numeric(15, 2), default=0, nullable=False)
    total_amount = Column(Numeric(15, 2), default=0, nullable=False)
    notes = Column(Text, nullable=True)
    warehouse_location = Column(String(100), nullable=True)

    # Relationships
    vendor = relationship("Vendor", back_populates="delivery_notes")
    lines = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
    )
    matching_results = relationship(
        "MatchingResult",
        foreign_keys="MatchingResult.dn_id",
        back_populates="delivery_note",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote(id={self.id}, dn_number={self.dn_number}, total={self.total_amount})>"


class DeliveryNoteLine(Base, TimestampMixin):
    """Delivery Note Line Item model."""

    __tablename__ = "delivery_note_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    delivery_note_id = Column(
        UUID(as_uuid=True), ForeignKey("delivery_notes.id", ondelete="CASCADE"), nullable=False
    )
    line_number = Column(Integer, nullable=False)
    product_code = Column(String(100), nullable=True, index=True)
    description = Column(Text, nullable=False)
    quantity_ordered = Column(Numeric(15, 4), default=0, nullable=False)
    quantity_delivered = Column(Numeric(15, 4), default=0, nullable=False)
    unit_of_measure = Column(String(20), default="EA", nullable=False)
    unit_price = Column(Numeric(15, 4), default=0, nullable=False)
    line_total = Column(Numeric(15, 2), default=0, nullable=False)
    notes = Column(Text, nullable=True)

    # Relationships
    delivery_note = relationship("DeliveryNote", back_populates="lines")
    match_line_results = relationship("MatchLineResult", back_populates="dn_line")

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine(id={self.id}, line_number={self.line_number}, product={self.product_code})>"

    def calculate_line_total(self) -> None:
        """Calculate line total."""
        self.line_total = self.quantity_delivered * self.unit_price
