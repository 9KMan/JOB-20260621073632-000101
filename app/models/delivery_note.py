// app/models/delivery_note.py
"""Delivery Note models for AP automation."""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
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
    from app.models.purchase_order import PurchaseOrder
    from app.models.match import Match, MatchLine
    from app.models.balance import BalanceLedger


class DeliveryNoteStatus(str):
    """Delivery Note status enumeration."""
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    RECEIVED = "RECEIVED"
    PARTIALLY_MATCHED = "PARTIALLY_MATCHED"
    MATCHED = "MATCHED"
    CANCELLED = "CANCELLED"


class DeliveryNote(Base):
    """Delivery Note (Goods Receipt) model."""
    
    __tablename__ = "delivery_notes"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    # Delivery Note identification
    dn_number: Mapped[str] = mapped_column(
        String(100),
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
    
    # Reference to PO
    po_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        ForeignKey("purchase_orders.po_number", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default=DeliveryNoteStatus.DRAFT,
        nullable=False,
        index=True,
    )
    
    # Dates
    shipment_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    
    receipt_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Reference
    reference_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Metadata
    created_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    source_system: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    
    source_document_id: Mapped[Optional[str]] = mapped_column(
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
    vendor: Mapped["Vendor"] = relationship(
        "Vendor",
        back_populates=None,
    )
    
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        foreign_keys=[po_number],
    )
    
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
    )
    
    matches: Mapped[list["Match"]] = relationship(
        "Match",
        back_populates="delivery_note",
    )
    
    balance_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="delivery_note",
    )
    
    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number}>"
    
    def to_dict(self, include_lines: bool = False) -> dict:
        """Convert delivery note to dictionary."""
        result = {
            "id": str(self.id),
            "dn_number": self.dn_number,
            "vendor_id": str(self.vendor_id),
            "po_number": self.po_number,
            "status": self.status,
            "shipment_date": self.shipment_date.isoformat() if self.shipment_date else None,
            "receipt_date": self.receipt_date.isoformat() if self.receipt_date else None,
            "reference_number": self.reference_number,
            "notes": self.notes,
            "created_by": self.created_by,
            "source_system": self.source_system,
            "source_document_id": self.source_document_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_lines:
            result["lines"] = [line.to_dict() for line in self.lines]
        
        return result


class DeliveryNoteLine(Base):
    """Delivery Note Line Item model."""
    
    __tablename__ = "delivery_note_lines"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    delivery_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
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
    
    # Reference
    po_line_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
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
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )
    
    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number}: {self.description[:30]}>"
    
    def to_dict(self) -> dict:
        """Convert DN line to dictionary."""
        return {
            "id": str(self.id),
            "delivery_note_id": str(self.delivery_note_id),
            "line_number": self.line_number,
            "sku": self.sku,
            "description": self.description,
            "quantity": self.quantity,
            "unit_of_measure": self.unit_of_measure,
            "po_line_reference": self.po_line_reference,
            "reference_line": self.reference_line,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
