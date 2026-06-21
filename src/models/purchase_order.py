// src/models/purchase_order.py
"""Purchase Order model."""
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.document import Document, DocumentType

if TYPE_CHECKING:
    pass


class PurchaseOrder(Document):
    """Purchase Order model."""
    
    __tablename__ = "purchase_orders"
    __mapper_args__ = {
        "polymorphic_identity": DocumentType.PURCHASE_ORDER,
    }
    
    # Extended PO fields
    payment_terms: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    delivery_address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    buyer_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    department: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    # Foreign key to parent document
    id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        primary_key=True,
    )
    
    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.document_number}>"


import uuid
