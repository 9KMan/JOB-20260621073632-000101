# models/__init__.py
"""Data models package.

This package contains SQLAlchemy ORM models for the AP Automation Engine.
All models inherit from a common Base class and include UUID primary keys,
timestamps, and proper indexing.
"""

from models.base import Base, TimestampMixin
from models.enums import (
    InvoiceStatus,
    PurchaseOrderStatus,
    DeliveryNoteStatus,
    MatchingDecision,
    MatchConfidence,
    LineMatchStatus,
    ExceptionType,
    ExceptionResolution,
    BalanceType,
)
from models.invoice import Invoice, InvoiceLine
from models.purchase_order import PurchaseOrder, PurchaseOrderLine
from models.delivery_note import DeliveryNote, DeliveryNoteLine
from models.balance_ledger import BalanceLedger
from models.cross_ref import CrossRef


__all__ = [
    # Base and mixins
    "Base",
    "TimestampMixin",
    # Enums
    "InvoiceStatus",
    "PurchaseOrderStatus",
    "DeliveryNoteStatus",
    "MatchingDecision",
    "MatchConfidence",
    "LineMatchStatus",
    "ExceptionType",
    "ExceptionResolution",
    "BalanceType",
    # Models
    "Invoice",
    "InvoiceLine",
    "PurchaseOrder",
    "PurchaseOrderLine",
    "DeliveryNote",
    "DeliveryNoteLine",
    "BalanceLedger",
    "CrossRef",
]
