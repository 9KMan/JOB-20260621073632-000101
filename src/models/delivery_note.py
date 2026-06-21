// src/models/delivery_note.py
"""Delivery Note and Delivery Note Line models."""
from decimal import Decimal
from datetime import date
from sqlalchemy import String, Numeric, Integer, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional, TYPE_CHECKING

from src.models.base import BaseModel
from src.models.enums import DocumentStatus, document_status_enum

if TYPE_CHECKING:
    from src.models.supplier import Supplier
    from src.models.purchase_order import PurchaseOrder
    from src.models.invoice import Invoice
    from src.models.matching import Match, BalanceEntry


class DeliveryNote(BaseModel):
    """Delivery Note header model."""
    
    __tablename__ = "delivery_notes"
    
    dn_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )
    
    supplier_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    
    po_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    delivery_date: Mapped[date] = mapped_column(
        Date(timezone=True),
        nullable=False,
        index=True
    )
    
    received_by: Mapped[str] = mapped_column(
        String(255),
        nullable=True
    )
    
    status: Mapped[DocumentStatus] = mapped_column(
        document_status_enum,
        default=DocumentStatus.DRAFT,
        nullable=False,
        index=True
    )
    
    notes: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True
    )
    
    # Relationships
    supplier: Mapped["Supplier"] = relationship(
        "Supplier",
        back_populates="delivery_notes"
    )
    
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        foreign_keys=[po_id],
        lazy="joined"
    )
    
    lines: Mapped[List["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="joined"
    )
    
    matched_invoices: Mapped[List["Match"]] = relationship(
        "Match",
        back_populates="delivery_note",
        foreign_keys="Match.dn_id",
        lazy="dynamic"
    )
    
    balance_entries: Mapped[List["BalanceEntry"]] = relationship(
        "BalanceEntry",
        back_populates="delivery_note",
        foreign_keys="BalanceEntry.dn_id",
        lazy="dynamic"
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_delivery_notes_supplier_status", "supplier_id", "status"),
        Index("ix_delivery_notes_delivery_date", "delivery_date"),
        Index("ix_delivery_notes_po_id", "po_id"),
    )
    
    def __repr__(self) -> str:
        return f"<DeliveryNote(id={self.id}, dn_number={self.dn_number})>"


class DeliveryNoteLine(BaseModel):
    """Delivery Note line item model."""
    
    __tablename__ = "delivery_note_lines"
    
    delivery_note_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    
    product_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )
    
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )
    
    quantity_delivered: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False
    )
    
    quantity_accepted: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=True
    )
    
    quantity_rejected: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        default=Decimal("0.000"),
        nullable=False
    )
    
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        default="EA",
        nullable=False
    )
    
    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines"
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_delivery_note_lines_dn_product", "delivery_note_id", "product_code"),
    )
    
    def __repr__(self) -> str:
        return f"<DeliveryNoteLine(id={self.id}, line_number={self.line_number}, product={self.product_code})>"
