// src/models/delivery_note.py
"""Delivery Note model."""
from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.document import Document, DocumentType

if TYPE_CHECKING:
    pass


class DeliveryNote(Document):
    """Delivery Note model."""
    
    __tablename__ = "delivery_notes"
    __mapper_args__ = {
        "polymorphic_identity": DocumentType.DELIVERY_NOTE,
    }
    
    # Delivery-specific fields
    delivery_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        index=True,
    )
    carrier: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    tracking_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    delivery_address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    received_by: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    is_partial_delivery: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    
    # Foreign key to parent document
    id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        primary_key=True,
    )
    
    def __repr__(self) -> str:
        return f"<DeliveryNote {self.document_number}>"


import uuid
from datetime import date
