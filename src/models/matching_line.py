# src/models/matching_line.py
"""Matching Line model for line-level matching details."""
from decimal import Decimal

from sqlalchemy import Column, String, Numeric, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.models.base import BaseModel


class MatchingLine(BaseModel):
    """Matching Line model for tracking line-level match details."""

    __tablename__ = "matching_lines"

    matching_record_id = Column(
        UUID(as_uuid=True),
        ForeignKey("matching_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Line references
    po_line_id = Column(UUID(as_uuid=True), nullable=True)
    invoice_line_id = Column(UUID(as_uuid=True), nullable=True)
    dn_line_id = Column(UUID(as_uuid=True), nullable=True)

    # Line details
    line_number = Column(Integer, nullable=False)
    item_code = Column(String(100), nullable=True)
    item_description = Column(String(500), nullable=True)

    # Quantities
    po_quantity = Column(Numeric(15, 3), nullable=True)
    invoice_quantity = Column(Numeric(15, 3), nullable=True)
    dn_quantity = Column(Numeric(15, 3), nullable=True)
    quantity_variance = Column(Numeric(15, 3), default=0, nullable=False)

    # Amounts
    po_amount = Column(Numeric(15, 2), nullable=True)
    invoice_amount = Column(Numeric(15, 2), nullable=True)
    dn_amount = Column(Numeric(15, 2), nullable=True)
    amount_variance = Column(Numeric(15, 2), default=0, nullable=False)

    # Match status
    match_status = Column(String(50), default="pending", nullable=False)
    match_type = Column(String(50), nullable=True)

    # Relationships
    matching_record = relationship("MatchingRecord", back_populates="line_matches")
