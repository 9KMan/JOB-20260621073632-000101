// app/models/purchase_order.py
"""Purchase Order models for PO management."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.vendor import Vendor
    from app.models.match import Match, MatchLine
    from app.models.balance import BalanceLedger


class POStatus(str):
    """Purchase Order status enumeration."""
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    SENT = "SENT"
    PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED"
    RECEIVED = "RECEIVED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class PurchaseOrder(Base):
    """Purchase Order model - single source of truth for 3-way matching."""
    
    __tablename__ = "purchase_orders"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    # PO identification
    po_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )
    
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vendors.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    
    # Status and workflow
    status: Mapped[str] = mapped_column(
        String(20),
        default=POStatus.DRAFT,
        nullable=False,
        index=True,
    )
    
    # Dates
    po_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    
    expected_delivery_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    actual_delivery_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Currency and amounts
    currency_code: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )
    
    subtotal: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    
    tax_amount: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    
    shipping_amount: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    
    total_amount: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        index=True,
    )
    
    # Amounts received/matched
    total_received: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    
    total_invoiced: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    
    total_paid: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    
    # Terms
    payment_terms_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    
    payment_terms_days: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    
    # Reference and notes
    reference_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    internal_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Metadata
    created_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    approved_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    is_locked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
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
    
    # Relationships
    vendor: Mapped["Vendor"] = relationship(
        "Vendor",
        back_populates="purchase_orders",
    )
    
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )
    
    matches: Mapped[list["Match"]] = relationship(
        "Match",
        back_populates="purchase_order",
    )
    
    balance_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="purchase_order",
    )
    
    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number}>"
    
    def to_dict(self, include_lines: bool = False) -> dict:
        """Convert PO to dictionary."""
        result = {
            "id": str(self.id),
            "po_number": self.po_number,
            "vendor_id": str(self.vendor_id),
            "status": self.status,
            "po_date": self.po_date.isoformat() if self.po_date else None,
            "expected_delivery_date": self.expected_delivery_date.isoformat() if self.expected_delivery_date else None,
            "actual_delivery_date": self.actual_delivery_date.isoformat() if self.actual_delivery_date else None,
            "currency_code": self.currency_code,
            "subtotal": self.subtotal,
            "tax_amount": self.tax_amount,
            "shipping_amount": self.shipping_amount,
            "total_amount": self.total_amount,
            "total_received": self.total_received,
            "total_invoiced": self.total_invoiced,
            "total_paid": self.total_paid,
            "payment_terms_code": self.payment_terms_code,
            "payment_terms_days": self.payment_terms_days,
            "reference_number": self.reference_number,
            "notes": self.notes,
            "is_locked": self.is_locked,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_lines:
            result["lines"] = [line.to_dict() for line in self.lines]
        
        return result


class PurchaseOrderLine(Base):
    """Purchase Order Line Item model."""
    
    __tablename__ = "purchase_order_lines"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    
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
        String(500),
        nullable=False,
    )
    
    quantity: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    
    unit_of_measure: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    
    # Pricing
    unit_price: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    
    line_total: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    
    # Delivered quantities
    quantity_received: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    
    quantity_invoiced: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    
    # Status
    is_complete: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    
    # Optional reference
    reference_line: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
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
    
    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )
    
    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number}: {self.description[:30]}>"
    
    def to_dict(self) -> dict:
        """Convert PO line to dictionary."""
        return {
            "id": str(self.id),
            "purchase_order_id": str(self.purchase_order_id),
            "line_number": self.line_number,
            "sku": self.sku,
            "description": self.description,
            "quantity": self.quantity,
            "unit_of_measure": self.unit_of_measure,
            "unit_price": self.unit_price,
            "line_total": self.line_total,
            "quantity_received": self.quantity_received,
            "quantity_invoiced": self.quantity_invoiced,
            "is_complete": self.is_complete,
            "reference_line": self.reference_line,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
