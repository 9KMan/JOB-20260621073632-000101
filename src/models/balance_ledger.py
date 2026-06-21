# src/models/balance_ledger.py
"""Balance Ledger model for tracking partial matches and balances."""
from decimal import Decimal

from sqlalchemy import Column, String, Numeric, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.models.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from src.models.purchase_order import PurchaseOrder
    from src.models.invoice import Invoice


class BalanceLedger(Base, UUIDMixin, TimestampMixin):
    """Balance Ledger model for tracking partial matches across documents."""
    
    __tablename__ = "balance_ledger"
    
    # Document references
    po_id = Column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    invoice_id = Column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    
    # Balance type: PO_OPEN, PO_INVOICED, PO_PAID, etc.
    balance_type = Column(String(30), nullable=False, index=True)
    
    # Document amounts
    po_total_amount = Column(Numeric(15, 2), nullable=False)
    invoice_amount = Column(Numeric(15, 2), nullable=True)
    matched_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    balance_amount = Column(Numeric(15, 2), nullable=False)
    
    # Quantities
    po_quantity = Column(Numeric(15, 3), nullable=False)
    invoiced_quantity = Column(Numeric(15, 3), default=Decimal("0.00"), nullable=False)
    delivered_quantity = Column(Numeric(15, 3), default=Decimal("0.00"), nullable=False)
    matched_quantity = Column(Numeric(15, 3), default=Decimal("0.00"), nullable=False)
    
    # Reference date
    as_of_date = Column(Date, nullable=False)
    
    # Status
    is_settled = Column(String(1), default="N", nullable=False)
    settled_date = Column(Date, nullable=True)
    
    # Notes
    notes = Column(String(500), nullable=True)
    
    # Relationships
    purchase_order = relationship(
        "PurchaseOrder",
        foreign_keys=[po_id],
        back_populates="balance_entries",
    )
    invoice = relationship(
        "Invoice",
        foreign_keys=[invoice_id],
        back_populates="balance_entries",
    )
    
    def __repr__(self) -> str:
        return f"<BalanceLedger(id={self.id}, balance_type={self.balance_type}, balance_amount={self.balance_amount})>"
