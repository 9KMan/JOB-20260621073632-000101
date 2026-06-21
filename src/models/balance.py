// src/models/balance.py
"""Balance tracking model for partial matches and settlements."""
import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Date, Numeric, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from src.models.base import Base, BaseModel

if TYPE_CHECKING:
    from src.models.purchase_order import PurchaseOrder
    from src.models.invoice import Invoice
    from src.models.delivery_note import DeliveryNote


class BalanceType(str, enum.Enum):
    """Type of balance tracking."""
    INVOICE_PO_VARIANCE = "invoice_po_variance"
    DELIVERY_PO_VARIANCE = "delivery_po_variance"
    PARTIAL_SHIPMENT = "partial_shipment"
    PARTIAL_INVOICE = "partial_invoice"
    OVERDELIVERY = "overdelivery"
    UNDERDELIVERY = "underdelivery"
    OVERINVOICE = "overinvoice"
    UNDERINVOICE = "underinvoice"
    DISPUTE = "dispute"
    CREDIT_NOTE = "credit_note"


class Balance(Base, BaseModel):
    """Balance ledger for tracking outstanding amounts across documents."""
    
    __tablename__ = "balances"
    
    balance_type: Mapped[str] = mapped_column(
        SQLEnum(BalanceType),
        nullable=False,
        index=True
    )
    
    # Document references
    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    delivery_note_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Original amounts
    original_po_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False
    )
    original_invoice_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True
    )
    original_delivery_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True
    )
    
    # Matched amounts
    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False
    )
    matched_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        default=Decimal("0.000"),
        nullable=False
    )
    
    # Outstanding balance
    outstanding_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False
    )
    outstanding_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        default=Decimal("0.000"),
        nullable=False
    )
    
    # Status
    is_resolved: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        index=True
    )
    resolution_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True
    )
    resolution_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # Reference to matching
    match_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True
    )
    
    # Item-level tracking (optional)
    item_code: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    
    # Relationships
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="balances"
    )
    invoice: Mapped[Optional["Invoice"]] = relationship(
        "Invoice",
        back_populates="balances"
    )
    delivery_note: Mapped[Optional["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="balances"
    )
    
    def __repr__(self) -> str:
        return f"<Balance(id={self.id}, type={self.balance_type}, outstanding={self.outstanding_amount})>"
