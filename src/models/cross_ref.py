# src/models/cross_ref.py
"""Cross Reference model for the learning loop functionality."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from models.invoice import Invoice
    from models.purchase_order import PurchaseOrder


class CrossRef(UUIDMixin, TimestampMixin, Base):
    """
    Cross Reference table for the learning loop.
    
    This table stores learned associations between:
    - Invoice/supplier combinations and PO numbers
    - Product codes and supplier item codes
    - Pricing patterns and historical matches
    
    The matching engine uses this table to improve future match accuracy.
    
    Attributes:
        id: Unique identifier (UUID)
        supplier_id: Supplier identifier
        invoice_number_pattern: Pattern from invoice number
        po_number: Associated purchase order number
        confirmed: Whether this association has been confirmed by human
        confirmation_count: Number of times this association was used
        rejection_count: Number of times this association was rejected
        last_used_at: Last time this cross-reference was used
        last_confirmed_at: Last human confirmation timestamp
        confidence_score: Calculated confidence (0-1)
        metadata: JSON field for additional data
    """
    
    __tablename__ = "cross_ref"
    __table_args__ = (
        Index("ix_cross_ref_supplier_id", "supplier_id"),
        Index("ix_cross_ref_po_number", "po_number"),
        Index("ix_cross_ref_supplier_invoice", "supplier_id", "invoice_number_pattern"),
        Index("ix_cross_ref_confirmed", "confirmed"),
        Index("ix_cross_ref_confidence", "confidence_score"),
    )
    
    supplier_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    supplier_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    invoice_number_pattern: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    po_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    product_code_invoice: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    product_code_po: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    confirmed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )
    confirmation_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    rejection_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    confidence_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )
    metadata_json: Mapped[dict | None] = mapped_column(
        Text,
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    
    # Relationships
    invoice_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
    )
    po_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    invoice: Mapped["Invoice | None"] = relationship(
        "Invoice",
        foreign_keys=[invoice_id],
        back_populates="cross_refs",
    )
    purchase_order: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder",
        foreign_keys=[po_id],
        back_populates="cross_refs",
    )
