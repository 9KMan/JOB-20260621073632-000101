// src/models/invoice.py
"""Invoice model."""
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.document import Document, DocumentType

if TYPE_CHECKING:
    pass


class Invoice(Document):
    """Invoice model."""
    
    __tablename__ = "invoices"
    __mapper_args__ = {
        "polymorphic_identity": DocumentType.INVOICE,
    }
    
    # Invoice-specific fields
    due_date: Mapped[Optional[Date]] = mapped_column(
        Date,
        nullable=True,
        index=True,
    )
    payment_method: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    bank_details: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    tax_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    
    # Discount fields
    discount_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    # Foreign key to parent document
    id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        primary_key=True,
    )
    
    def __repr__(self) -> str:
        return f"<Invoice {self.document_number}>"


import uuid
from decimal import Decimal
