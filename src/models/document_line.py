// src/models/document_line.py
"""Document line item model."""
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.database import Base

if TYPE_CHECKING:
    from src.models.document import Document


class DocumentLine(Base):
    """Line item within a document (PO, Invoice, or Delivery Note)."""
    
    __tablename__ = "document_lines"
    __table_args__ = (
        UniqueConstraint("document_id", "line_number", name="uq_document_line_number"),
    )
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    
    # Foreign keys
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Line identification
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    
    # Product/Service information
    sku: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        default="EA",
        nullable=False,
    )
    
    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    # Delivery information (for DN)
    delivered_quantity: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 4),
        nullable=True,
    )
    
    # Matching
    matched_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0"),
        nullable=False,
    )
    
    # Relationships
    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="lines",
    )
    
    @property
    def open_quantity(self) -> Decimal:
        """Calculate open (unmatched) quantity."""
        return self.quantity - self.matched_quantity
    
    @property
    def is_fully_matched(self) -> bool:
        """Check if line is fully matched."""
        return self.matched_quantity >= self.quantity
    
    def __repr__(self) -> str:
        return f"<DocumentLine {self.document_id}:{self.line_number}>"


import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import DateTime, func
from typing import Optional
