// src/app/models/balance_ledger.py
"""Balance ledger for tracking partial matches and remaining balances."""

from sqlalchemy import Column, String, Numeric, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from src.app.models.base import BaseModel


class BalanceType(str, enum.Enum):
    """Balance type enumeration."""

    INVOICE = "INVOICE"
    DELIVERY_NOTE = "DELIVERY_NOTE"
    PURCHASE_ORDER = "PURCHASE_ORDER"


class BalanceLedger(BaseModel):
    """Balance ledger tracking remaining amounts for partial matches."""

    __tablename__ = "balance_ledger"

    # Document reference
    document_type = Column(String(20), nullable=False)
    document_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    document_number = Column(String(50), nullable=False)

    # Balance tracking
    balance_type = Column(String(20), nullable=False)
    original_amount = Column(Numeric(15, 2), nullable=False)
    matched_amount = Column(Numeric(15, 2), nullable=False, default=0)
    remaining_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")

    # Reference to the match that created this balance entry
    match_result_id = Column(
        UUID(as_uuid=True), ForeignKey("match_results.id", ondelete="SET NULL"), nullable=True
    )

    # Status
    is_settled = Column(String(10), nullable=False, default="FALSE")

    def __repr__(self) -> str:
        return f"<BalanceLedger(id={self.id}, document_number={self.document_number}, remaining={self.remaining_amount})>"
