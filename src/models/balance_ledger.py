# src/models/balance_ledger.py
"""Balance Ledger model for tracking partial matches and balances."""
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Column, String, Numeric, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.purchase_order import PurchaseOrder
    from src.models.invoice import Invoice
    from src.models.delivery_note import DeliveryNote


class BalanceLedger(BaseModel):
    """Balance Ledger model for tracking balances across documents."""

    __tablename__ = "balance_ledger"

    # Document references
    document_type = Column(String(20), nullable=False, index=True)  # PO, INV, DN
    document_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    purchase_order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Balance tracking
    original_amount = Column(Numeric(15, 2), nullable=False)
    matched_amount = Column(Numeric(15, 2), default=0, nullable=False)
    remaining_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)

    # Status
    status = Column(String(50), default="open", nullable=False, index=True)
    balance_date = Column(Date, nullable=False)

    # Reference
    reference_document_type = Column(String(20), nullable=True)
    reference_document_id = Column(UUID(as_uuid=True), nullable=True)
    reference_matching_id = Column(UUID(as_uuid=True), nullable=True)

    # Relationships
    purchase_order = relationship("PurchaseOrder")
